import requests
from bs4 import BeautifulSoup
from langchain.tools import tool
from models import Company

@tool
def google_search_companies(query: str) -> list[dict]:
    """ابحث عن شركات سعودية من خلال Google. 
    مثال: 'شركات تقنية في الرياض'"""
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    search_url = f"https://www.google.com/search?q={query}+site:linkedin.com+OR+site:yellowpages.com.sa&num=20"
    
    results = []
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for result in soup.select('.g'):
            title = result.select_one('h3')
            link = result.select_one('a')
            snippet = result.select_one('.VwiC3b')
            
            if title and link:
                results.append({
                    "name": title.get_text(),
                    "url": link.get('href', ''),
                    "description": snippet.get_text() if snippet else ""
                })
    except Exception as e:
        return [{"error": str(e)}]
    
    return results[:10]