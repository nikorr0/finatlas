from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import json

def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument("--ignore-certificate-errors")  # Ignore SSL certificate errors
    chrome_options.add_argument("--ignore-ssl-errors")  # Ignore SSL errors
    chrome_options.add_argument("--disable-notifications")  # Disable notifications
    chrome_options.add_argument("--disable-popup-blocking")  # Disable popup blocking
    chrome_options.add_argument("--disable-infobars")  # Disable infobars
    chrome_options.add_argument("--disable-extensions")  # Disable extensions
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    chrome_options.add_argument("--no-sandbox")  # Disable sandbox mode
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument('--ignore-urlfetcher-cert-requests')
    chrome_options.add_argument('--mute-audio')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--ignore-certificate-errors-spki-list')
    chrome_options.add_argument('--no-zygote')
    chrome_options.add_argument('--disable-web-security')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    return driver

def get_header():
  with open('resources/header.json') as f:
      header = json.load(f)
  return header

class element_has_right_name(object):
  def __init__(self, locator):
    self.locator = locator

  def __call__(self, driver):
    element = driver.find_element(*self.locator) 
    org_name = element.text.lower()
    if org_name != 'информация о плане финансово-хозяйственной деятельности':
        return element
    else:
        return False

class is_loader_on_page(object):
  def __init__(self, locator):
    self.locator = locator

  def __call__(self, driver):
    try:
        element = driver.find_element(*self.locator) 
        return False
    except:
        return True
    
class element_has_error_name(object):
  def __init__(self, locator):
    self.locator = locator

  def __call__(self, driver):
    element = driver.find_element(*self.locator) 
    text = element.text.lower()
    if "невозможно" in text:
        return element
    else:
        return False
  
def remove_double_spaces_regex(s):
    return re.sub(r' {2,}', ' ', s).strip().lstrip()

def format_organization_name(org_name):
    org_name = remove_double_spaces_regex(org_name)
    if '"' in org_name:
        symbols_count = 0
        for symbol in org_name:
            if symbol == '"':
                symbols_count += 1
        if symbols_count >= 3:
            formatted_name = org_name.split('"', maxsplit=1)[-1]
        else:
            formatted_name = org_name.split('"')[-2]
    else:
        formatted_name = org_name.split('высшего образования')[-1]
        if "области" in formatted_name:
            formatted_name = formatted_name.split("области")[-1]
            
    formatted_name = re.sub(r'\s*-\s*', '-', formatted_name)
    formatted_name = formatted_name.strip().upper()
    
    return formatted_name