import requests
from bs4 import BeautifulSoup
import pdfplumber
import re
from urllib.parse import urljoin
import os
from data_collection.pdf_parser import get_name_and_year_from_pdf
from data_collection.utils import get_header

HEADERS = get_header()
FILE_KEYWORDS = ['финансово-хозяйственной', 'fhd', 'фхд', 'финансово', 'finansovo', 'fxd']
 
def download_correct_file(website_url, allowed_years=None):
    try:
        response = requests.get(website_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Handle redirects if needed
    if "window.parent.location.replace(" in soup.prettify():
        redirect_url = soup.prettify().split("window.parent.location.replace(")[1].split(");")[0].strip("'\"")
        try:
            response = requests.get(redirect_url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
        except:
            return None
    
    # Find all PDF links with relevant keywords
    pdf_links = list()
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith('.pdf'):
            if any(keyword in href.lower() for keyword in FILE_KEYWORDS):
                # Extract year from the link

                year_match = re.search(r'20\d\d', href)
                if year_match:
                    if allowed_years is not None:
                        if str(year_match.group(0)) not in allowed_years:
                            continue
                        else:
                            pdf_links.append(urljoin(website_url, href))
                    else:
                        pdf_links.append(urljoin(website_url, href))
                        
    # Return the newest files (one per year)
    if pdf_links:
        return pdf_links
    return None

def check_file_readability(file_path_or_url, allowed_years=None):
    readability = None
    try:
        # If it's a URL, download temporarily
        if file_path_or_url.startswith('http'):
            response = requests.get(file_path_or_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            with open('temp.pdf', 'wb') as f:
                f.write(response.content)
            file_to_check = 'temp.pdf'
        else:
            file_to_check = file_path_or_url
        
        # Try to read the PDF
        with pdfplumber.open(file_to_check) as pdf:
            if len(pdf.pages) == 0:
                readability = False
                return readability
            # Try to extract name
            for n_page in range(len(pdf.pages)):
                try:
                    page_text = pdf.pages[n_page].extract_text().lower()
                except:
                    continue
                if "от 17.08.2020 n 168н" in page_text:
                    break
            
            _, plan_year, _  = get_name_and_year_from_pdf(page_text=page_text, return_plan_year=True)
            
            if allowed_years is not None:
                if plan_year not in allowed_years:
                    readability = False
                    return readability
            
            readability = plan_year is not None and len(plan_year) > 0
            return readability
            
    except Exception as e:
        return False
    finally:
        # if not readability:
        # Clean up temporary file if created
        if 'file_to_check' in locals() and file_to_check == 'temp.pdf':
            if os.path.exists(file_to_check):
                os.remove(file_to_check)
