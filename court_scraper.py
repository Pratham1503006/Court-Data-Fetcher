import time, re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import json

class CourtScraper:
    def __init__(self):
        opts = Options()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)
        opts.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.driver = webdriver.Chrome(options=opts)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self.base_url = "https://delhihighcourt.nic.in/app/get-case-type-status"

    def search_case(self, case_type, case_number, filing_year):
        try:
            self.driver.get(self.base_url)
            
            # Wait for the form to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.NAME, "case_type"))
            )
            
            # Fill case type dropdown
            case_type_dropdown = Select(self.driver.find_element(By.NAME, "case_type"))
            case_type_dropdown.select_by_visible_text(case_type)
            
            # Fill case number
            case_number_field = self.driver.find_element(By.NAME, "case_number")
            case_number_field.clear()
            case_number_field.send_keys(case_number)
            
            # Fill year dropdown
            year_dropdown = Select(self.driver.find_element(By.NAME, "case_year"))
            year_dropdown.select_by_visible_text(str(filing_year))
            
            # Handle CAPTCHA
            print("\n" + "="*60)
            print("           CAPTCHA VERIFICATION REQUIRED")
            print("="*60)
            print(f"Please look at the browser window for the CAPTCHA image.")
            print("Enter the CAPTCHA code you see below:")
            
            captcha_code = input("CAPTCHA Code: ").strip()
            
            # Find and fill CAPTCHA input field
            captcha_field = self.driver.find_element(By.ID, "captchaInput")
            captcha_field.clear()
            captcha_field.send_keys(captcha_code)
            
            # Click submit button
            submit_button = self.driver.find_element(By.ID, "search")
            submit_button.click()
            
            # Wait for results
            print("Searching for case details...")
            time.sleep(5)
            
            # Check for results table
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            return self._parse_results()
            
        except Exception as e:
            return {"success": False, "error": f"Search failed: {str(e)}"}
    

    def _parse_results(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Look for results table
            results_table = soup.find('table')
            
            if not results_table:
                return {"success": False, "error": "No results table found"}
            
            # Check if "No data available" message exists
            if "No data available in table" in soup.get_text():
                return {"success": False, "error": "No case found with the provided details"}
            
            # Extract case information from table rows
            rows = results_table.find_all('tr')[1:]  # Skip header row
            
            if not rows:
                return {"success": False, "error": "No case data found"}
            
            # Process the first result (most relevant)
            first_row = rows[0]
            cells = first_row.find_all('td')
            
            if len(cells) < 3:
                return {"success": False, "error": "Incomplete case data"}
            
            # Extract case details
            case_info = self._extract_case_details(cells)
            
            # Look for additional details by clicking on case if available
            view_link = first_row.find('a', text=re.compile('view|details', re.IGNORECASE))
            if view_link:
                case_info.update(self._get_detailed_case_info(view_link.get('href')))
            
            return {
                "success": True,
                "petitioner": case_info.get('petitioner', 'Not found'),
                "respondent": case_info.get('respondent', 'Not found'),
                "filing_date": case_info.get('filing_date'),
                "next_hearing_date": case_info.get('next_hearing_date'),
                "status": case_info.get('status', 'Active'),
                "documents": case_info.get('documents', []),
                "case_number": case_info.get('case_number', 'Not found'),
                "court_number": case_info.get('court_number', 'Not specified'),
                "raw_html": str(soup)[:5000]  # Limit raw HTML size
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error parsing results: {str(e)}"}

    def _extract_case_details(self, cells):
        """Extract case details from table cells"""
        case_details = {}
        
        try:
            # Column 1: S.No. (skip)
            # Column 2: Diary No. / Case No.[STATUS]
            if len(cells) > 1:
                case_no_cell = cells[1].get_text(strip=True)
                case_details['case_number'] = case_no_cell.split('[')[0].strip()
                if '[' in case_no_cell and ']' in case_no_cell:
                    status_match = re.search(r'\[(.*?)\]', case_no_cell)
                    if status_match:
                        case_details['status'] = status_match.group(1)
            
            # Column 3: Petitioner Vs. Respondent
            if len(cells) > 2:
                parties_cell = cells[2].get_text(strip=True)
                if ' Vs. ' in parties_cell or ' V/s ' in parties_cell or ' vs ' in parties_cell:
                    # Split petitioner and respondent
                    separator = ' Vs. ' if ' Vs. ' in parties_cell else (' V/s ' if ' V/s ' in parties_cell else ' vs ')
                    parties = parties_cell.split(separator, 1)
                    case_details['petitioner'] = parties[0].strip()
                    case_details['respondent'] = parties[1].strip() if len(parties) > 1 else 'Not specified'
                else:
                    case_details['petitioner'] = parties_cell
                    case_details['respondent'] = 'Not specified'
            
            # Column 4: Listing Date / Court No.
            if len(cells) > 3:
                listing_info = cells[3].get_text(strip=True)
                # Try to extract date
                date_match = re.search(r'(\d{1,2}[-./]\d{1,2}[-./]\d{2,4})', listing_info)
                if date_match:
                    case_details['next_hearing_date'] = date_match.group(1)
                
                # Try to extract court number
                court_match = re.search(r'Court[:\s]*(\d+|[IVX]+)', listing_info, re.IGNORECASE)
                if court_match:
                    case_details['court_number'] = court_match.group(1)
                else:
                    case_details['court_number'] = listing_info
            
        except Exception as e:
            print(f"Error extracting case details: {e}")
        
        return case_details

    def _get_detailed_case_info(self, detail_url):
        """Get additional case information from detail page"""
        additional_info = {}
        
        try:
            if detail_url and not detail_url.startswith('http'):
                detail_url = 'https://delhihighcourt.nic.in' + detail_url
            
            self.driver.get(detail_url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Look for case history or order information
            case_history = soup.find('div', class_='case-history') or soup.find('table')
            
            if case_history:
                # Extract filing date
                filing_date_text = case_history.find(text=re.compile('fil(ing|ed)', re.IGNORECASE))
                if filing_date_text:
                    parent = filing_date_text.parent
                    date_match = re.search(r'(\d{1,2}[-./]\d{1,2}[-./]\d{2,4})', parent.get_text())
                    if date_match:
                        additional_info['filing_date'] = date_match.group(1)
                
                # Extract document links
                documents = []
                pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
                
                for link in pdf_links:
                    doc_url = link.get('href')
                    if not doc_url.startswith('http'):
                        doc_url = 'https://delhihighcourt.nic.in' + doc_url
                    
                    documents.append({
                        'type': 'Order/Judgment',
                        'url': doc_url,
                        'text': link.get_text(strip=True) or 'Court Document',
                        'date': self._extract_date_from_text(link.get_text())
                    })
                
                additional_info['documents'] = documents
            
        except Exception as e:
            print(f"Error getting detailed info: {e}")
        
        return additional_info

    def _extract_date_from_text(self, text):
        """Extract date from text"""
        if not text:
            return None
        
        date_patterns = [
            r'(\d{1,2}[-./]\d{1,2}[-./]\d{4})',
            r'(\d{1,2}[-./]\d{1,2}[-./]\d{2})',
            r'(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None

    def _find_text(self, soup, keywords):
        """Find text based on keywords"""
        for keyword in keywords:
            element = soup.find(text=re.compile(keyword, re.IGNORECASE))
            if element and element.parent:
                sibling = element.parent.find_next_sibling()
                if sibling:
                    return sibling.get_text(strip=True)
        return "Not found"

    def _find_date(self, soup, keywords):
        """Find date based on keywords"""
        text = self._find_text(soup, keywords)
        return self._extract_date_from_text(text)

    def _extract_docs(self, soup):
        """Extract document links from soup"""
        documents = []
        
        # Look for PDF links
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        for link in pdf_links:
            doc_url = link.get('href')
            if not doc_url.startswith('http'):
                doc_url = 'https://delhihighcourt.nic.in' + doc_url
            
            documents.append({
                'type': 'PDF Document',
                'url': doc_url,
                'text': link.get_text(strip=True) or 'Court Document',
                'date': self._extract_date_from_text(link.get_text())
            })
        
        # Look for order/judgment links
        order_links = soup.find_all('a', text=re.compile('order|judgment|copy', re.IGNORECASE))
        
        for link in order_links:
            doc_url = link.get('href')
            if doc_url and not doc_url.startswith('http'):
                doc_url = 'https://delhihighcourt.nic.in' + doc_url
            
            if doc_url:
                documents.append({
                    'type': 'Order/Judgment',
                    'url': doc_url,
                    'text': link.get_text(strip=True),
                    'date': self._extract_date_from_text(link.get_text())
                })
        
        # Sort documents by date (most recent first)
        documents_with_dates = [doc for doc in documents if doc['date']]
        documents_without_dates = [doc for doc in documents if not doc['date']]
        
        documents_with_dates.sort(key=lambda x: x['date'], reverse=True)
        
        return documents_with_dates + documents_without_dates

    def __del__(self):
        try: 
            self.driver.quit()
        except: 
            pass
    
    
