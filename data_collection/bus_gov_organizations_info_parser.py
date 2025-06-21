from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from data_collection.utils import initialize_driver
from packages.utils import remove_double_spaces_regex
from data_collection.utils import is_loader_on_page
from data_collection.utils import element_has_right_name
import pandas as pd
    
# Function to extract data 
def extract_organization_info(driver):
    data = dict()

    # Полученная Страница (Page)
    data["Страница"] = driver.current_url

    # Тип учреждения 
    try:
        data["Тип учреждения"] = driver.find_element(By.XPATH, "//div[contains(text(), 'Тип учреждения')]/following-sibling::div").text
    except:
        data["Тип учреждения"] = None

    # Признак доведения субсидий 
    try:
        data["Признак доведения субсидий"] = driver.find_element(By.XPATH, "//div[contains(text(), 'Признак доведения субсидий')]/following-sibling::div").text
    except:
        data["Признак доведения субсидий"] = None

    # Вид учреждения
    try:
        data["Вид учреждения"] = driver.find_element(By.XPATH, "//div[contains(text(), 'Вид учреждения')]/following-sibling::div").text
    except:
        data["Вид учреждения"] = None

    # Основные виды деятельности по ОКВЭД 
    try:
        data["Основные виды деятельности по ОКВЭД"] = ", ".join(driver.find_element(By.XPATH, "//div[contains(text(), 'Основные виды деятельности по ОКВЭД')]/following-sibling::div").text.strip().split("\n"))
    except:
        data["Основные виды деятельности по ОКВЭД"] = None

    # Иные виды деятельности по ОКВЭД 
    try:
        toggle_list_button = None
        # Ожидание, пока кнопка переключения станет кликабельной
        try:
            toggle_list_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Отобразить полный перечень видов деятельности')]"))
            )
            
            toggle_list_button.click()

            # Ожидание загрузки дополнительного контента
            toggle_list_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Скрыть полный перечень видов деятельности')]"))
            )
        except:
            pass
        
        # Поиск раздела "Иные виды деятельности по ОКВЭД"
        section = driver.find_element(By.XPATH, "//div[contains(text(), 'Иные виды деятельности по ОКВЭД')]")
        values = ", ".join(section.find_elements(By.XPATH, "./following-sibling::div")[0].text.strip().split("\n"))
        
        # Удаление "Скрыть полный перечень видов деятельности", если была кнопка 
        if toggle_list_button is not None:
            values.pop(-1)

        # Сохранение извлеченных значений в словарь
        data["Иные виды деятельности по ОКВЭД"] = values
            
    except:
        data["Иные виды деятельности по ОКВЭД"] = None

    # Адрес фактического местонахождения 
    try:
        data["Адрес фактического местонахождения"] = driver.find_element(By.XPATH, "//div[contains(text(), 'Адрес фактического местонахождения')]/following-sibling::div").text
    except:
        data["Адрес фактического местонахождения"] = None

    # Сайт учреждения 
    try:
        org_link = driver.find_element(By.XPATH, "//div[contains(text(), 'Сайт учреждения')]/following-sibling::div").text.strip()
        if (org_link == "http://") or (org_link == "https://"):
            org_link = None
        if (org_link is not None) and (org_link[-1] != "/"):
            org_link += "/"
        
        data["Сайт учреждения"] = org_link
        
    except:
        data["Сайт учреждения"] = None

    # Адрес электронной почты 
    try:
        data["Адрес электронной почты"] = driver.find_element(By.XPATH, "//div[contains(text(), 'Адрес электронной почты')]/following-sibling::div").text
    except:
        data["Адрес электронной почты"] = None

    # Широта и Долгота 
    try:
        data["Широта"] = float(driver.find_element(By.XPATH, "//div[contains(text(), 'Широта')]/following-sibling::div").text)
        data["Долгота"] = float(driver.find_element(By.XPATH, "//div[contains(text(), 'Долгота')]/following-sibling::div").text)
        
    except Exception as e:
        print(f"Error extracting coordinates: {e}")
        data["Широта"] = None
        data["Долгота"] = None

    return data

# Main function
def extract_organizations_data(urls):
    # ignore security warnings
    driver = initialize_driver()

    # словарь
    university_links = {}

    try:
        for url in urls:
            # Remove "/plans"
            clean_url = url.replace("/plans", "")
            
            driver.get(clean_url)
            
            # проверка загрузки информации на странице (не продолжаем пока есть колесо загрузки)
            loader = WebDriverWait(driver, 10).until(is_loader_on_page((By.CLASS_NAME, 'loader')))
            
            organization_elem = WebDriverWait(driver, 10).until(element_has_right_name((By.CLASS_NAME, 'title.title_bold')))
            organization_fullname = remove_double_spaces_regex(organization_elem.text).lower()

            data = extract_organization_info(driver)

            # сохранить в словарь
            university_links[organization_fullname] = [[key, value] for key, value in data.items()]

    finally:
        # закрыт driver
        driver.quit()

    return university_links

def drop_irrelevant(x):
    if x == "Университет":
        return x
    elif x == "Академия":
        return x
    elif x == "Институт":
        return x

def transform_to_dataframe(university_links, drop_invalid_type_org=False):
    university_links_data = dict()
    university_links_data['name'] = list()
    university_links_data['gov_link'] = list()
    university_links_data['org_kind'] = list()
    university_links_data['subsidy'] = list()
    university_links_data['org_type'] = list()
    university_links_data['main_activities'] = list()
    university_links_data['other_activities'] = list()
    university_links_data['address'] = list()
    university_links_data['org_link'] = list()
    university_links_data['plan_link'] = list()
    university_links_data['email'] = list()
    university_links_data['latitude'] = list()
    university_links_data['longitude'] = list()

    for name in list(university_links.keys()):
        university_links_data['name'].append(name)

        for col in university_links[name]:
            if col[1] == "":
                col[1] = None
                
            if col[0] == "Страница":
                university_links_data['gov_link'].append(col[1])
            elif col[0] == "Тип учреждения":
                university_links_data['org_kind'].append(col[1])
            elif col[0] == "Признак доведения субсидий":
                university_links_data['subsidy'].append(col[1])
            elif col[0] == "Вид учреждения":
                university_links_data['org_type'].append(col[1])
            elif col[0] == "Основные виды деятельности по ОКВЭД":
                university_links_data['main_activities'].append(col[1].replace("\n", ", "))
            elif col[0] == "Иные виды деятельности по ОКВЭД":
                if type(col[1]) is list:
                    university_links_data['other_activities'].append(", ".join(col[1]))
                else:
                    university_links_data['other_activities'].append(col[1])
            elif col[0] == "Адрес фактического местонахождения":
                university_links_data['address'].append(col[1])
            elif col[0] == "Сайт учреждения":
                if (col[1] == "http://") or (col[1] == "https://"):
                    col[1] = None
                university_links_data['org_link'].append(col[1])
            elif col[0] == "Адрес электронной почты":
                university_links_data['email'].append(col[1])
            elif col[0] == "Широта":
                university_links_data['latitude'].append(col[1])
            elif col[0] == "Долгота":
                university_links_data['longitude'].append(col[1])
            elif col[0] == "Страница с ПФХД":
                university_links_data['plan_link'].append(col[1])
    
    university_links_data = pd.DataFrame(university_links_data)
    
    if drop_invalid_type_org:
        university_links_data['org_type'] = university_links_data['org_type'].apply(drop_irrelevant)
        university_links_data = university_links_data.dropna(subset="org_type")
        
    return university_links_data