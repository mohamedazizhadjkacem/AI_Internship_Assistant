import time
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


def scrape_linkedin(job_title: str, location: str, last_24_hours: bool = False):
    """
    Scrapes LinkedIn for internship listings using Selenium, including full job descriptions.
    """
    print(f"🚀 Starting LinkedIn scrape for '{job_title}' in '{location}'")
    
    # --- Configure Selenium Chrome options ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = None
    try:
                # Initialize the Chrome driver using webdriver-manager to automatically handle the driver executable.
        # Point to the manually downloaded chromedriver.
        service = ChromeService(executable_path="drivers/chromedriver.exe")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(45)

        # Construct search URL
        search_query = f"{job_title} internship"
        url = (
            f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(search_query)}"
            f"&location={quote_plus(location)}&sortBy=R"
        )
        if last_24_hours:
            url += "&f_TPR=r86400"

        print(f"Navigating to search results: {url}")
        driver.get(url)
        time.sleep(3) # Allow initial page load

        # Scroll to load all jobs
        scroll_pause_time = 2
        scrolls = 5 # Limit scrolls to avoid excessive loading
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        print("Scrolling to load all results...")
        for i in range(scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("Reached end of results.")
                break
            last_height = new_height
            print(f"Scroll {i+1}/{scrolls} complete.")

        # Parse job cards
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        job_cards = soup.find_all('div', class_='base-card')

        if not job_cards:
            print("⚠️ No job cards found. LinkedIn may have changed its layout or blocked the request.")
            # Save the page source for debugging
            try:
                with open("linkedin_search_results.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("📄 Saved page HTML to linkedin_search_results.html for debugging.")
                driver.save_screenshot('linkedin_error.png')
                print("📸 Saved screenshot to linkedin_error.png for debugging.")
            except Exception as e:
                print(f"Could not save debug files: {e}")
            return []

        print(f"✅ Found {len(job_cards)} job cards. Fetching details for each...")
        job_listings = []

        for i, card in enumerate(job_cards):
            try:
                title_elem = card.find('h3', class_='base-search-card__title')
                company_elem = card.find('h4', class_='base-search-card__subtitle')
                link_elem = card.find('a', class_='base-card__full-link')
                
                if all([title_elem, company_elem, link_elem]):
                    job_url = link_elem['href'].split('?')[0]  # Clean URL
                    job_title_text = title_elem.get_text(strip=True)
                    company_name_text = company_elem.get_text(strip=True)
                    
                    # Skip entries where title or company are just asterisks
                    if re.fullmatch(r'\*+', job_title_text) or re.fullmatch(r'\*+', company_name_text):
                        print(f"Skipping masked entry: {job_title_text} at {company_name_text}")
                        continue
                    
                    print(f"\n--- Processing Job {i+1}/{len(job_cards)}: {job_title_text} at {company_name_text} ---")
                    
                    # Fetch the full description using our detailed function
                    # NOTE: This creates a new driver for each job to ensure isolation and avoid bans.
                    full_description = _fetch_full_description(job_url, job_title_text)
                    
                    job_listings.append({
                        'job_title': job_title_text,
                        'company_name': company_name_text,
                        'source_url': job_url,
                        'application_link': job_url,  # Often the same, can be refined later
                        'job_description': clean_description_text(full_description),
                        'source_site': 'LinkedIn'
                    })
            except Exception as e:
                print(f"❌ Error processing a job card: {e}")
                continue
        
        print(f"\n🏁 Scrape finished. Returning {len(job_listings)} fully detailed jobs.")
        return job_listings

    except WebDriverException as e:
        error_msg = f"A WebDriver error occurred: {e}"
        print(f"❌ {error_msg}")
        return {'error': error_msg}
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        print(f"❌ {error_msg}")
        return {'error': error_msg}
    finally:
        if driver:
            driver.quit()


def _fetch_full_description(job_url: str, job_title: str) -> str:
    """Opens the job detail page in a fresh headless driver, expands description and returns text."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    try:
        # Point to the manually downloaded chromedriver.
        service = ChromeService(executable_path="drivers/chromedriver.exe")
        with webdriver.Chrome(service=service, options=chrome_options) as temp_driver:
            temp_driver.set_page_load_timeout(30)
            temp_driver.get(job_url)
            print(f"📄 Page loaded for description: {temp_driver.title[:80]}...")
            time.sleep(3)

            # Strategy 1: Handle Auth Walls/Login prompts
            try:
                current_url = temp_driver.current_url
                if "authwall" in current_url or "login" in current_url or "checkpoint" in current_url:
                    print("⚠️ Detected login wall or auth challenge")
                    # Simple script to remove modals/overlays. Might not work for all cases.
                    temp_driver.execute_script("""
                        const modals = document.querySelectorAll('[role="dialog"], .modal, .overlay');
                        modals.forEach(modal => modal.remove());
                        const overlays = document.querySelectorAll('.overlay, .backdrop');
                        overlays.forEach(overlay => overlay.remove());
                    """)
                    time.sleep(2)
            except Exception as e:
                print(f"⚠️ Error handling auth wall: {e}")

            # Strategy 2: Find the most likely description element
            description_selectors = [
                ".show-more-less-html__markup", ".jobs-description-content__text", ".jobs-box__html-content",
                ".jobs-description__content", ".description__text", "[data-job-description]",
                ".jobs-description", ".job-description"
            ]
            description_element = None
            for selector in description_selectors:
                try:
                    elements = temp_driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        # Find the element with the most text, as it's likely the main description
                        best_element = max(elements, key=lambda el: len(el.text))
                        if len(best_element.text.strip()) > 50: # Basic quality check
                            description_element = best_element
                            print(f"✅ Found description container using: {selector}")
                            break
                except NoSuchElementException:
                    continue
            
            if not description_element:
                return "Description element not found on page."

            # Strategy 3: Try to expand the description ("Show more" button)
            try:
                # This selector is common for LinkedIn's "Show more" button
                show_more_button = temp_driver.find_element(By.CSS_SELECTOR, "button[data-tracking-control-name='show-more']")
                temp_driver.execute_script("arguments[0].click();", show_more_button)
                print("✅ Clicked 'Show more' button to expand description.")
                time.sleep(1) # Wait for content to load
            except NoSuchElementException:
                print("ⓘ 'Show more' button not found, description may be complete.")
            except Exception as e:
                print(f"⚠️ Error clicking 'Show more' button: {e}")

            # Strategy 4: Get the final, clean text
            final_text = description_element.text.strip()
            print(f"📏 Final description length: {len(final_text)} characters")
            
            # Strategy 5: Validate quality
            validate_description_quality(final_text, job_title)
            
            return final_text

    except Exception as e:
        print(f"❌ ERROR fetching description for {job_url}: {e}")
        return f"Error fetching description: {e}"


def validate_description_quality(description: str, job_title: str) -> dict:
    """Enhanced validation of extracted job description quality"""
    clean_desc = re.sub(r'\s+', ' ', description.lower().strip())
    quality_metrics = {
        'length': len(description),
        'word_count': len(description.split()),
        'has_requirements': bool(re.search(r'\b(requirements?|qualifications?|skills?|experience)\b', clean_desc)),
        'has_responsibilities': bool(re.search(r'\b(responsibilities|duties|role|tasks)\b', clean_desc)),
        'has_benefits': bool(re.search(r'\b(benefits|compensation|salary|perks)\b', clean_desc)),
        'has_company_info': bool(re.search(r'\b(company|about us|our mission)\b', clean_desc)),
        'truncation_indicators': bool(re.search(r'(\.\.\.|…|show more|voir plus)', clean_desc)),
        'completeness_score': 0
    }
    score = 0
    
    # Length scoring
    if quality_metrics['length'] > 2000:
        score += 4
    elif quality_metrics['length'] > 1500:
        score += 3
    elif quality_metrics['length'] > 1000:
        score += 2
    elif quality_metrics['length'] > 500:
        score += 1
    
    # Content completeness
    if quality_metrics['has_requirements']:
        score += 2
    if quality_metrics['has_responsibilities']:
        score += 2
    if quality_metrics['has_benefits']:
        score += 1
    if quality_metrics['has_company_info']:
        score += 1
    if not quality_metrics['truncation_indicators']:
        score += 1
    
    quality_metrics['completeness_score'] = score
    
    # Print quality report
    print(f"\n📊 QUALITY REPORT for '{job_title}':")
    print(f"  📏 Length: {quality_metrics['length']} chars, {quality_metrics['word_count']} words")
    print(f"  ✅ Has requirements: {quality_metrics['has_requirements']}")
    print(f"  ✅ Has responsibilities: {quality_metrics['has_responsibilities']}")
    print(f"  ✅ Has benefits: {quality_metrics['has_benefits']}")
    print(f"  ✅ Has company info: {quality_metrics['has_company_info']}")
    print(f"  ⚠️ Truncation indicators: {quality_metrics['truncation_indicators']}")
    print(f"  🎯 Completeness score: {quality_metrics['completeness_score']}/11")
    
    return quality_metrics


def clean_description_text(description: str) -> str:
    """Clean and format the extracted description text"""
    if not description:
        return ""
    cleaned = re.sub(r'\n\s*\n', '\n', description).strip()
    artifacts_to_remove = [r'Show more\s*Show less', r'Voir plus\s*Voir moins']
    for pattern in artifacts_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


# Test execution
if __name__ == "__main__":
    test_job_url = (
        "https://www.linkedin.com/jobs/view/software-engineer-intern-at-onlyworks-4250042720/?refId=0Zc595Ymwv8qFgtlU8mtWQ%3D%3D&trackingId=jDgI4nRTrufZjtkUqW0bww%3D%3D"
    )

    job_listings = scrape_linkedin("Software Engineer", "New York", last_24_hours=True)
    
    if job_listings:
        print(f"\n📝 EXTRACTED JOB LISTINGS:")
        print("=" * 80)
        for job in job_listings:
            print(f"Job Title: {job['job_title']}")
            print(f"Company: {job['company_name']}")
            print(f"Description: {job['job_description'][:2000]}")  # Show first 2000 chars
            if len(job['job_description']) > 2000:
                print(f"\n... (showing first 2000 of {len(job['job_description'])} characters)")
            print("=" * 80)
    else:
        print(f"\n❌ EXTRACTION FAILED: {job_listings}")