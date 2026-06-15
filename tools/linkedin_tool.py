import requests
from langchain.tools import tool
import os

PROXYCURL_API_KEY = os.getenv("PROXYCURL_API_KEY")

@tool
def get_linkedin_company_data(linkedin_url: str) -> dict:
    """جلب بيانات شركة من LinkedIn عبر Proxycurl API.
    يستخرج: عدد الموظفين، الصناعة، آخر نشاط"""
    
    api_endpoint = "https://nubela.co/proxycurl/api/linkedin/company"
    
    try:
        response = requests.get(
            api_endpoint,
            params={"url": linkedin_url, "extra": "include", "funding_data": "include"},
            headers={"Authorization": f"Bearer {PROXYCURL_API_KEY}"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "employee_count": data.get("company_size_on_linkedin"),
                "industry": data.get("industry"),
                "headquarters": data.get("hq", {}).get("city"),
                "founded": data.get("founded_year"),
                "follower_count": data.get("follower_count"),
                "specialties": data.get("specialities", [])[:5]
            }
    except Exception as e:
        return {"error": str(e)}
    
    return {"error": "Failed to fetch"}