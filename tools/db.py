import psycopg2
import os

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def create_tables():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            website TEXT,
            email VARCHAR(255),
            phone VARCHAR(50),
            sector VARCHAR(100),
            city VARCHAR(100),
            employee_count VARCHAR(50),
            linkedin_url TEXT,
            twitter_handle VARCHAR(100),
            source VARCHAR(100),
            status VARCHAR(50) DEFAULT 'new',
            scraped_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS social_posts (
            id SERIAL PRIMARY KEY,
            company_id INT REFERENCES companies(id),
            platform VARCHAR(50),
            content TEXT,
            posted_at TIMESTAMP,
            url TEXT
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def insert_company(company: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO companies (name, website, email, phone, sector, city, employee_count, linkedin_url, source)
        VALUES (%(name)s, %(website)s, %(email)s, %(phone)s, %(sector)s, %(city)s, %(employee_count)s, %(linkedin_url)s, %(source)s)
        ON CONFLICT (email) DO UPDATE SET scraped_at = NOW()
        RETURNING id
    """, company)
    
    company_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return company_id