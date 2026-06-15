from playwright.sync_api import sync_playwright
from langchain.tools import tool
import re

@tool  
def scrape_company_website(url: str) -> dict:
    """استخرج معلومات الاتصال من موقع شركة.
    يستخرج: الإيميل، الهاتف، العنوان"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=15000)
            page.wait_for_load_state('networkidle', timeout=10000)
            content = page.content()
            text = page.inner_text('body')
            
            # استخراج الإيميل
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
            
            # استخراج رقم الهاتف السعودي
            phones = re.findall(r'(?:\+966|00966|0)?[0-9]{9,10}', text)
            
            # استخراج الوصف
            meta_desc = page.query_selector('meta[name="description"]')
            description = meta_desc.get_attribute('content') if meta_desc else ""
            
            browser.close()
            return {
                "url": url,
                "email": emails[0] if emails else None,
                "phone": phones[0] if phones else None,
                "description": description[:300]
            }
        except Exception as e:
            browser.close()
            return {"url": url, "error": str(e)}