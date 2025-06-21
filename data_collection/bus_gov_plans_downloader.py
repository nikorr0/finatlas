from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from datetime import datetime
from packages.utils import remove_double_spaces_regex
from data_collection.utils import initialize_driver
from data_collection.utils import element_has_right_name
from logger.log_config import logger_print

def download_html_tables_from_url(url, org_name=None, years_to_parse=None, save_to="resources/ПФХД_html/", driver=None):
    # пример ссылки = "https://bus.gov.ru/agency/459662/plans"
    
    if years_to_parse is None:
        years_to_parse = list(map(lambda x: str(x), range(2022, datetime.now().year + 1)))
        
    years_to_parse.reverse()
        
    universities_plans_data = dict()
    universities_plans_data['name'] = list()
    universities_plans_data['plan_year'] = list()
    universities_plans_data['plan_filename'] = list()
    universities_plans_data['org_link'] = list()
    universities_plans_data['html_table_link'] = list()
    universities_plans_data['file_extension'] = list()
    
    if driver is None:
        driver = initialize_driver()
 
    if url[len(url) - 6:] != "/plans":
        if url[-1] != "/":
            url += "/"
        url += "plans"
    # переход по ссылке 
    driver.get(url)
    
    organization_elem = WebDriverWait(driver, 10).until(element_has_right_name((By.CLASS_NAME, 'title.title_bold')))
    if org_name is None:
        organization_fullname = remove_double_spaces_regex(organization_elem.text).lower()
    if org_name is not None:
        organization_fullname = org_name
    year_found = True
    
    for year in years_to_parse:
        
        if year_found:
            # нажатие по списку годов
            try:
                year_list_dropdown = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'mat-select-trigger'))
                )
                year_list_dropdown.click()
            except: 
                logger_print("ПРЕДУПРЕЖДЕНИЕ: Список годов не найден")

        # нажатие на определенный год в списке
        try:
            year_element = WebDriverWait(driver, 0.7).until(
                EC.presence_of_element_located((By.XPATH, f"//span[text()=' {year} год ']"))
            )
            year_element.click()
            year_found = True
        except:
            year_found = False
            logger_print(f'ПРЕДУПРЕЖДЕНИЕ: Год {year} не найден')
            continue
        
        # нажатие на кнопку с html таблицей ПФХД
        print_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 
                'button.button_split.button_size_small.button_type_print.float-r'))
        )
        print_button.click()

        # переключение на окно с html таблицей ПФХД
        new_window = driver.window_handles[-1]
        driver.switch_to.window(new_window)

        html_table_url = driver.current_url
        filename = str(round(time.time(), 2)).replace(".", "_")
        filename += f"_{year}.html"
        
        with open(save_to + filename, "w+", encoding="utf-8") as f:
            f.write(driver.page_source)

        universities_plans_data['name'].append(organization_fullname)
        universities_plans_data['file_extension'].append('html')
        universities_plans_data['plan_year'].append(year)
        universities_plans_data['plan_filename'].append(filename)
        universities_plans_data['org_link'].append(url.replace("/plans", ""))
        universities_plans_data['html_table_link'].append(html_table_url)
        
        # закрытие окна с html таблицей ПФХД
        try:
            driver.close()
            new_window = driver.window_handles[-1]
            driver.switch_to.window(new_window)
        except:
            driver = initialize_driver()
            driver.get(url)

    return pd.DataFrame(universities_plans_data)   