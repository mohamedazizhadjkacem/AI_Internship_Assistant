import requests
from bs4 import BeautifulSoup
import streamlit as st
import re

# --- LinkedIn Scraper ---

# NOTE: Web scraping is fragile. LinkedIn can (and will) change its HTML structure,
# which will break this scraper. It may also temporarily block your IP if you make too many requests.
# A real-world, robust scraper would use proxy rotation, more advanced user-agent spoofing,
# and potentially a headless browser like Selenium.

@st.cache_data(ttl=3600)  # Cache results for 1 hour to avoid re-scraping
def scrape_linkedin(job_title: str, location: str = "Canada", last_24_hours: bool = False):
    """Scrapes LinkedIn for internship listings.

    Args:
        job_title: The job title keyword(s) to search.
        location: Location string (default "United States").
        last_24_hours: If True, only return jobs posted in the last 24 hours.
    """
    search_query = f"{job_title} internship"
    url = (
        f"https://www.linkedin.com/jobs/search/?keywords={search_query.replace(' ', '%20')}"
        f"&location={location.replace(' ', '%20')}"
        f"&sortBy=R"  # Most recent first
    )
    if last_24_hours:
        url += "&f_TPR=r86400"  # Only jobs posted in the last 24 hours
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        return {'error': f"Failed to retrieve data from LinkedIn: {e}"}

    soup = BeautifulSoup(response.content, 'html.parser')
    
    job_listings = []
    # Find all job posting cards. The class name might need updating if LinkedIn changes its layout.
    job_cards = soup.find_all('div', class_='base-card')

    if not job_cards:
        return {'error': 'No job cards found. LinkedIn may have changed its layout or blocked the request.'}

    for card in job_cards:
        try:
            title_elem = card.find('h3', class_='base-search-card__title')
            company_elem = card.find('h4', class_='base-search-card__subtitle')
            link_elem = card.find('a', class_='base-card__full-link')
            
            if not all([title_elem, company_elem, link_elem]):
                continue

            title_text = title_elem.get_text(strip=True)
            company_text = company_elem.get_text(strip=True)

            # Fallback: sometimes the <h4> contains only ***** but the nested <a> has the real name
            if re.fullmatch(r'\*+', company_text):
                anchor = company_elem.find('a')
                if anchor:
                    company_text = anchor.get_text(strip=True)

            # Skip results clearly masked (company or title are only asterisks)
            if re.fullmatch(r'\*+', title_text) or re.fullmatch(r'\*+', company_text):
                continue

            job_listings.append({
                'job_title': title_text,
                'company_name': company_text,
                'application_link': link_elem['href'],
                'source_site': 'LinkedIn'
            })
        except Exception:
            # Ignore cards that can't be parsed
            continue
            
    return job_listings
