"""
Saudi Arabia Company Scraping Agent
====================================
Target: ~500 companies across all sectors + startups
Output: Structured CSV with clean columns
"""

import os
import csv
import re
import json
import time
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated
import operator
import requests
from bs4 import BeautifulSoup

load_dotenv()

# ─────────────────────────────────────────────
# QUERIES — 50+ queries to reach ~500 companies
# ─────────────────────────────────────────────
QUERIES = [

    # ── Information Technology ──
    ("software companies Saudi Arabia Riyadh", "Information Technology"),
    ("hardware IT services companies Saudi Arabia", "Information Technology"),
    ("tech startups Saudi Arabia Riyadh 2024", "Information Technology"),
    ("cybersecurity companies Saudi Arabia", "Information Technology"),
    ("cloud computing companies Saudi Arabia", "Information Technology"),
    ("AI artificial intelligence startups Saudi Arabia", "Information Technology"),
    ("SaaS software startups Saudi Arabia", "Information Technology"),
    ("ERP enterprise software Saudi Arabia", "Information Technology"),
    ("data analytics companies Saudi Arabia", "Information Technology"),
    ("mobile app development companies Saudi Arabia", "Information Technology"),

    # ── Financials ──
    ("banks financial institutions Saudi Arabia", "Financials"),
    ("fintech startups Saudi Arabia 2024", "Financials"),
    ("insurance companies Saudi Arabia", "Financials"),
    ("asset management investment Saudi Arabia", "Financials"),
    ("Islamic finance companies Saudi Arabia", "Financials"),
    ("payment solutions startups Saudi Arabia", "Financials"),
    ("digital banking neobank Saudi Arabia", "Financials"),
    ("venture capital private equity Saudi Arabia", "Financials"),

    # ── Health Care ──
    ("hospitals healthcare providers Saudi Arabia", "Health Care"),
    ("pharmaceutical companies Saudi Arabia", "Health Care"),
    ("biotechnology startups Saudi Arabia", "Health Care"),
    ("medical devices companies Saudi Arabia", "Health Care"),
    ("telemedicine health tech startups Saudi Arabia", "Health Care"),
    ("dental clinics chains Saudi Arabia", "Health Care"),
    ("mental health wellness startups Saudi Arabia", "Health Care"),

    # ── Consumer Discretionary ──
    ("retail ecommerce companies Saudi Arabia", "Consumer Discretionary"),
    ("restaurants food chains Saudi Arabia", "Consumer Discretionary"),
    ("hotels hospitality companies Saudi Arabia", "Consumer Discretionary"),
    ("automotive car companies Saudi Arabia", "Consumer Discretionary"),
    ("fashion apparel brands Saudi Arabia", "Consumer Discretionary"),
    ("luxury goods retail Saudi Arabia", "Consumer Discretionary"),
    ("sports fitness companies Saudi Arabia", "Consumer Discretionary"),
    ("travel tourism startups Saudi Arabia", "Consumer Discretionary"),

    # ── Communication Services ──
    ("telecom companies Saudi Arabia", "Communication Services"),
    ("media broadcasting companies Saudi Arabia", "Communication Services"),
    ("digital media content startups Saudi Arabia", "Communication Services"),
    ("gaming entertainment companies Saudi Arabia", "Communication Services"),
    ("advertising marketing agencies Saudi Arabia", "Communication Services"),
    ("OTT streaming platforms Saudi Arabia", "Communication Services"),

    # ── Industrials ──
    ("construction companies Saudi Arabia", "Industrials"),
    ("aerospace defense companies Saudi Arabia", "Industrials"),
    ("logistics transportation companies Saudi Arabia", "Industrials"),
    ("manufacturing companies Saudi Arabia", "Industrials"),
    ("engineering consultancy Saudi Arabia", "Industrials"),
    ("smart city infrastructure startups Saudi Arabia", "Industrials"),

    # ── Consumer Staples ──
    ("food beverage companies Saudi Arabia", "Consumer Staples"),
    ("FMCG consumer goods Saudi Arabia", "Consumer Staples"),
    ("supermarket grocery chains Saudi Arabia", "Consumer Staples"),
    ("personal care household products Saudi Arabia", "Consumer Staples"),

    # ── Energy ──
    ("oil gas companies Saudi Arabia", "Energy"),
    ("renewable energy solar companies Saudi Arabia", "Energy"),
    ("clean energy startups Saudi Arabia", "Energy"),
    ("petrochemical companies Saudi Arabia", "Energy"),
    ("energy storage battery startups Saudi Arabia", "Energy"),

    # ── Materials ──
    ("chemicals companies Saudi Arabia", "Materials"),
    ("mining companies Saudi Arabia", "Materials"),
    ("construction materials Saudi Arabia", "Materials"),
    ("packaging materials companies Saudi Arabia", "Materials"),

    # ── Utilities ──
    ("electricity water utilities Saudi Arabia", "Utilities"),
    ("waste management companies Saudi Arabia", "Utilities"),
    ("smart grid water tech startups Saudi Arabia", "Utilities"),

    # ── Real Estate ──
    ("real estate development companies Saudi Arabia", "Real Estate"),
    ("property management Saudi Arabia", "Real Estate"),
    ("proptech real estate startups Saudi Arabia", "Real Estate"),
    ("REIT real estate investment Saudi Arabia", "Real Estate"),

    # ── Startups / General ──
    ("Y Combinator startups Saudi Arabia", "Startups"),
    ("Saudi startups Series A funding 2024", "Startups"),
    ("Saudi Vision 2030 startups companies", "Startups"),
    ("NEOM startups technology companies", "Startups"),
    ("Saudi Aramco Wa'ed portfolio companies", "Startups"),
    ("STC Ventures portfolio startups Saudi Arabia", "Startups"),
    ("Sanabil investments portfolio Saudi Arabia", "Startups"),
    ("food delivery startups Saudi Arabia", "Startups"),
    ("edtech education startups Saudi Arabia", "Startups"),
    ("legaltech startups Saudi Arabia", "Startups"),
    ("hrtech recruitment startups Saudi Arabia", "Startups"),
    ("insurtech startups Saudi Arabia", "Startups"),
    ("agritech food tech startups Saudi Arabia", "Startups"),
]

# ─────────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────────
@tool
def google_search_companies(query: str) -> list:
    """Search Google for Saudi companies. Returns list of company info."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    results = []
    try:
        url = f"https://www.google.com/search?q={query}&num=10"
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')

        for g in soup.select('.g')[:8]:
            title = g.select_one('h3')
            link = g.select_one('a')
            snippet = g.select_one('.VwiC3b')
            if title and link:
                href = link.get('href', '')
                if href.startswith('/url?q='):
                    href = href.split('/url?q=')[1].split('&')[0]
                results.append({
                    "name": title.get_text(strip=True),
                    "url": href,
                    "description": snippet.get_text(strip=True) if snippet else ""
                })
    except Exception as e:
        results = [{"error": str(e)}]

    time.sleep(1.5)  # polite delay
    return results


@tool
def scrape_company_website(url: str) -> dict:
    """Scrape company website for contact info: email, phone, description."""
    if not url or not url.startswith('http'):
        return {"url": url, "error": "Invalid URL"}

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(separator=' ')

        emails = re.findall(r'[\w\.\-]+@[\w\.\-]+\.[a-zA-Z]{2,}', text)
        emails = [e for e in emails if not e.endswith(('.png', '.jpg', '.svg'))]

        phones = re.findall(r'(?:\+966|00966|05|5)[0-9\s\-]{8,12}', text)

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc['content'][:200] if meta_desc and meta_desc.get('content') else ""

        city = ""
        for c in ['Riyadh', 'Jeddah', 'Dammam', 'Mecca', 'Medina', 'Khobar', 'Neom']:
            if c.lower() in text.lower():
                city = c
                break

        return {
            "url": url,
            "email": emails[0] if emails else "N/A",
            "phone": phones[0].strip() if phones else "N/A",
            "description": description,
            "city": city or "Saudi Arabia"
        }
    except Exception as e:
        return {"url": url, "error": str(e), "email": "N/A", "phone": "N/A"}


# ─────────────────────────────────────────────
# AGENT STATE
# ─────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    query: str
    sector: str


tools = [google_search_companies, scrape_company_website]
llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=4096)
llm_with_tools = llm.bind_tools(tools)


def orchestrator(state: AgentState):
    system_prompt = f"""You are a B2B data collection agent specializing in Saudi Arabian companies.

Sector: {state['sector']}
Query: {state['query']}

Your task:
1. Use google_search_companies to find companies matching this query
2. For the top 5-8 companies found, use scrape_company_website to get contact details
3. Return results as a JSON array with this EXACT structure for each company:

[
  {{
    "company_name": "English name",
    "arabic_name": "Arabic name if known",
    "sector": "{state['sector']}",
    "sub_sector": "specific sub-industry",
    "city": "city name",
    "country": "Saudi Arabia",
    "website": "https://...",
    "email": "email or N/A",
    "phone": "phone or N/A",
    "linkedin_url": "linkedin URL or N/A",
    "employees": "employee count or range",
    "founded_year": "year or N/A",
    "description": "2-3 sentence description",
    "is_startup": true/false,
    "is_listed": true/false,
    "tags": ["tag1", "tag2"]
  }}
]

Return ONLY the JSON array, no other text. All fields in English."""

    response = llm_with_tools.invoke([
        {"role": "system", "content": system_prompt},
        *state["messages"]
    ])
    return {"messages": [response]}


def should_continue(state: AgentState):
    last = state["messages"][-1]
    if hasattr(last, 'tool_calls') and last.tool_calls:
        return "tools"
    return END


def build_agent():
    wf = StateGraph(AgentState)
    wf.add_node("orchestrator", orchestrator)
    wf.add_node("tools", ToolNode(tools))
    wf.set_entry_point("orchestrator")
    wf.add_conditional_edges("orchestrator", should_continue)
    wf.add_edge("tools", "orchestrator")
    return wf.compile()


def run_agent(query: str, sector: str) -> list:
    agent = build_agent()
    result = agent.invoke({
        "messages": [{"role": "user", "content": f"Find companies: {query}"}],
        "query": query,
        "sector": sector
    })
    last_msg = result["messages"][-1].content

    # Extract JSON from response
    try:
        match = re.search(r'\[.*\]', last_msg, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return []


# ─────────────────────────────────────────────
# DEDUPLICATION
# ─────────────────────────────────────────────
def deduplicate(companies: list) -> list:
    seen = set()
    unique = []
    for c in companies:
        key = c.get('company_name', '').lower().strip()
        website = c.get('website', '').lower().strip()
        identifier = website if website != 'n/a' and website else key
        if identifier and identifier not in seen:
            seen.add(identifier)
            unique.append(c)
    return unique


# ─────────────────────────────────────────────
# SAVE TO CSV
# ─────────────────────────────────────────────
FIELDNAMES = [
    'company_name', 'arabic_name', 'sector', 'sub_sector',
    'city', 'country', 'website', 'email', 'phone',
    'linkedin_url', 'employees', 'founded_year',
    'description', 'is_startup', 'is_listed', 'tags'
]


def save_csv(companies: list, path: str):
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction='ignore')
        writer.writeheader()
        for c in companies:
            row = {k: c.get(k, 'N/A') for k in FIELDNAMES}
            if isinstance(row['tags'], list):
                row['tags'] = ', '.join(row['tags'])
            writer.writerow(row)
    print(f"💾 Saved {len(companies)} companies → {path}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    output_path = os.path.expanduser("~/Desktop/saudi_companies_500.csv")

    print("=" * 60)
    print("🇸🇦  Saudi Arabia Company Scraping Agent")
    print(f"📋  Target: ~500 companies | {len(QUERIES)} queries")
    print("=" * 60)

    all_companies = []
    total_queries = len(QUERIES)

    for i, (query, sector) in enumerate(QUERIES, 1):
        print(f"\n[{i}/{total_queries}] 🔍 [{sector}] {query}")

        try:
            companies = run_agent(query, sector)
            if companies:
                all_companies.extend(companies)
                print(f"  ✅ Found {len(companies)} companies | Total so far: {len(all_companies)}")
            else:
                print(f"  ⚠️  No results")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

        # Save checkpoint every 10 queries
        if i % 10 == 0:
            unique = deduplicate(all_companies)
            save_csv(unique, output_path)
            print(f"\n📊 Checkpoint: {len(unique)} unique companies saved")

        time.sleep(2)

    # Final save
    unique_companies = deduplicate(all_companies)
    save_csv(unique_companies, output_path)

    # Summary
    sectors = {}
    startups = sum(1 for c in unique_companies if c.get('is_startup') is True)
    for c in unique_companies:
        s = c.get('sector', 'Unknown')
        sectors[s] = sectors.get(s, 0) + 1

    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    print(f"Total unique companies: {len(unique_companies)}")
    print(f"Startups identified:    {startups}")
    print("\nBy sector:")
    for s, count in sorted(sectors.items(), key=lambda x: -x[1]):
        print(f"  {s:<30} {count}")
    print(f"\n✅ File saved to: {output_path}")
