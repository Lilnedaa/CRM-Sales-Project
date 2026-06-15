from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Company(BaseModel):
    name: str
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    sector: Optional[str] = None
    city: Optional[str] = None
    employee_count: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    source: str
    scraped_at: datetime = datetime.now()

class SocialPost(BaseModel):
    company_name: str
    platform: str  # twitter, linkedin
    content: str
    posted_at: Optional[str] = None
    url: Optional[str] = None