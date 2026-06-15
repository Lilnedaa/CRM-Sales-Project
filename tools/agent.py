from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_anthropic import ChatAnthropic
from typing import TypedDict, Annotated
import operator

from tools.google_tool import google_search_companies
from tools.website_tool import scrape_company_website
from tools.linkedin_tool import get_linkedin_company_data

# --- تعريف الـ State ---
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    companies_found: list
    query: str

# --- الـ Tools ---
tools = [
    google_search_companies,
    scrape_company_website,
    get_linkedin_company_data
]

# --- الـ Model ---
llm = ChatAnthropic(model="claude-sonnet-4-20250514")
llm_with_tools = llm.bind_tools(tools)

# --- الـ Nodes ---
def orchestrator(state: AgentState):
    """الـ Orchestrator يقرر الخطوة التالية"""
    system_prompt = """أنت agent متخصص في جمع بيانات الشركات السعودية.
    مهمتك:
    1. ابحث عن الشركات باستخدام google_search_companies
    2. لكل شركة، اسكرب موقعها باستخدام scrape_company_website  
    3. جلب بيانات LinkedIn إذا توفر الرابط
    4. اجمع كل المعلومات وأعدها بشكل منظم
    
    ابدأ الآن."""
    
    response = llm_with_tools.invoke([
        {"role": "system", "content": system_prompt},
        *state["messages"]
    ])
    return {"messages": [response]}

def should_continue(state: AgentState):
    """هل نكمل أم ننهي؟"""
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return END

# --- بناء الـ Graph ---
def build_agent():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("orchestrator", orchestrator)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.set_entry_point("orchestrator")
    workflow.add_conditional_edges("orchestrator", should_continue)
    workflow.add_edge("tools", "orchestrator")
    
    return workflow.compile()

# --- تشغيل الـ Agent ---
def run_scraping_agent(query: str):
    agent = build_agent()
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": f"ابحث عن: {query}"}],
        "companies_found": [],
        "query": query
    })
    
    return result