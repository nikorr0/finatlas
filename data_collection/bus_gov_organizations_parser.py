from data_collection.utils import element_has_error_name, is_loader_on_page, element_has_right_name
from data_collection.utils import initialize_driver
from bus_gov_organizations_info_parser import extract_organization_info
from bus_gov_plans_parser import download_html_tables_from_url

# Сбор организаций с сайта bus.gov.ru на странице со всеми вузами (фильтры), 
# на сайте может быть отображено всего 1000 организаций,
# в апреле 2025 года было собрано 835 организаций с учетом филиалов и остальных (550 только вузов)

WAIT_TIMEOUT = 5

def safe_click(element_locator, timeout=WAIT_TIMEOUT):
    """Безопасный клик по элементу с явным ожиданием"""
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(element_locator)
    )
    element.click()

def change_page_size():
    """Изменение количества отображаемых элементов на странице"""
    safe_click((By.CSS_SELECTOR, "mat-select.items-per-page-select"))
    safe_click((By.XPATH, "//span[text()=' 30 ']"))

def collect_organizations_data():
    """Основная функция сбора данных об организациях"""
    collected_organizations = []
    while True:
        try:                
            page_source_code = driver.page_source
            soup = BeautifulSoup(page_source_code, "html.parser")
            all_elems = soup.find_all('app-citizen-organizations-list-card')
            
            if len(all_elems) == 0:
                break
            
            for elem in all_elems:
                soup_elem = BeautifulSoup(str(elem), "html.parser")   
                name = soup_elem.select_one('.citizen-organizations-card-title-text a').text.lower()
                # Извлечение ссылки на страницу организации
                details_link = "https://bus.gov.ru" + soup_elem.select_one('.citizen-organizations-card-title-text a')['href']
                # Извлечение ссылки на сайт организации
                try:
                    website_link = soup_elem.select_one('.citizen-organizations-card-website a')['href']
                except:
                    website_link = ""
                    
                collected_organizations.append([name, details_link, website_link])

            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, "info-section-paginator__next.ng-star-inserted"))
            ).click()
            
            try:
                WebDriverWait(driver, 1).until(element_has_error_name((By.CLASS_NAME, 'title.title_bold')))
                break
            except:
                continue
                
        except Exception as e:
            break
    
    return collected_organizations

import time


# Пример работы:
# link = "https://bus.gov.ru/search/citizen-organizations?regions=5277349,%205277385,%205277388,%205277403,%205277339,%205277355,%205277409,%205277363,%205277318,%205277319,%205277397,%205277320,%205277356,%205277340,%205277321,%205277361,%20101262418,%205277407,%205277394,%20101262416,%205277322,%205277350,%205277389,%205277351,%205277341,%205277360,%205277323,%205277404,%205277352,%205277337,%205277390,%205277369,%205277338,%205277324,%205277353,%205277398,%20100039651,%205277378,%205277325,%205277342,%205277326,%20101262417,%205277405,%205277364,%205277365,%205277335,%205277327,%205277343,%205277345,%205277370,%205277346,%205277391,%205277392,%205277371,%205277328,%205277372,%205277373,%205277401,%205277344,%205277357,%205277329,%205277374,%205277347,%205277375,%205277400,%205277406,%205277383,%20100039652,%205277359,%205277330,%205277354,%205277331,%205277366,%205277332,%205277393,%205277333,%205277386,%205277379,%205277367,%205277376,%205277402,%205277387,%205277381,%20101262415,%205277380,%205277358,%205277368,%205277408,%205277382,%205277334&areas=empty&vguIds=1279&vguName=1006000%20%D0%9E%D0%B1%D1%80%D0%B0%D0%B7%D0%BE%D0%B2%D0%B0%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D0%BE%D0%B5%20%D1%83%D1%87%D1%80%D0%B5%D0%B6%D0%B4%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%B2%D1%8B%D1%81%D1%88%D0%B5%D0%B3%D0%BE%20%D0%BF%D1%80%D0%BE%D1%84%D0%B5%D1%81%D1%81%D0%B8%D0%BE%D0%BD%D0%B0%D0%BB%D1%8C%D0%BD%D0%BE%D0%B3%D0%BE%20%D0%BE%D0%B1%D1%80%D0%B0%D0%B7%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F"

# driver = initialize_driver()
# driver.get(link)

# time.sleep(2)
# start_time = time.time()

# change_page_size()
# time.sleep(1)
# collected_data = list()
# collected_data.extend(collect_organizations_data())

# print("Затраченное время:", time.time() - start_time)

# print(len(collected_data))
# print(collected_data)


# import re

# def remove_double_spaces_regex(s):
#     return re.sub(r' {2,}', ' ', s).strip().lstrip()

# import time

# time_to_parse_from_info_card = list()
# time_to_parse_from_agency = list()

# university_links = dict()
# universities_plans_data = dict()

# driver = initialize_driver()

# ignore_name_words = ["филиал", "центр", "комбинат", "клиника", "часть", "база", "комплекс"]

# for i, organization in enumerate(collected_data):    
#     print(f"№{i} " + organization[0])
    
#     skip_org = False
#     for word in ignore_name_words:
#         if word in organization[0]:
#             skip_org = True
#             break
    
#     if skip_org:
#         print("Пропуск...")
#         continue
    
#     # if ("образования" not in organization[0]) and ("бюджетное" not in organization[0]):
#     if ("образования" not in organization[0]) and ("образовательное" not in organization[0]):
#         print("Пропуск...")
#         continue
    
#     # num of tries
#     error_occured = False
#     for i in range(3):
#         try:
#             if error_occured:
#                 driver = initialize_driver()
                
#             # время 1
#             start_time_from_info_card = time.time()
#             driver.get(organization[1])
#             agency_link_element = WebDriverWait(driver, 10).until(
#                 EC.presence_of_element_located((By.CLASS_NAME, "basic-link"))
#             )
#             agency_link = agency_link_element.get_property('href')
#             print(agency_link)
            
#             # время 2
#             time.sleep(1)
#             start_time_from_agency = time.time()
#             driver.get(agency_link)
            
#             # проверка загрузки информации на странице (не продолжаем пока есть колесо загрузки)
#             loader = WebDriverWait(driver, 10).until(is_loader_on_page((By.CLASS_NAME, 'loader')))
            
#             organization_elem = WebDriverWait(driver, 10).until(element_has_right_name((By.CLASS_NAME, 'title.title_bold')))
#             organization_fullname = remove_double_spaces_regex(organization_elem.text).lower()

#             data = extract_organization_info(driver)
#             if data["Вид учреждения"] is None:
#                 error_occured = True
#                 print("error_occured")
#                 try:
#                     driver.quit()
#                 except:
#                     pass
#                 continue
#             # сохранить в словарь
#             university_links[organization_fullname] = [[key, value] for key, value in data.items()]
            
#             universities_plans_data_one = download_html_tables_from_url(agency_link, save_to="resources/ПФХД_html/", driver=driver)
#             universities_plans_data[organization_fullname] = [[key, value] for key, value in universities_plans_data_one.items()]
            
#             time_to_parse_from_info_card.append(time.time() - start_time_from_info_card)
#             time_to_parse_from_agency.append(time.time() - start_time_from_agency)
#             break
#         except:
#             error_occured = True
#             print("error_occured")
#             try:
#                 driver.quit()
#             except:
#                 pass
#             continue
        

# Cбор всех организаций по регионам
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import pickle


# Константы
ORGS_STORAGE_FILENAME = 'orgs_storage.pickle'
BASE_URL = "https://bus.gov.ru/search/citizen-organizations?regions=empty&areas=empty" # "https://bus.gov.ru/search/citizen-organizations?vguIds=1249&vguName=1000000%20%D0%9E%D0%B1%D1%80%D0%B0%D0%B7%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5&vguSubElements=true"
WAIT_TIMEOUT = 2  # Базовый таймаут ожидания элементов в секундах

# Нажать на "Все параметры поиска →"/"Свернуть параметры"
def expand_search_area():
    WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/ui-view/div/div/div[2]/app-main-search/div/a"))
                    ).click()

def safe_click(element_locator, timeout=WAIT_TIMEOUT):
    """Безопасный клик по элементу с явным ожиданием"""
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(element_locator)
    )
    element.click()

def open_filter_dropdown(filter_name):
    """
    Открытие выпадающего списка фильтра по названию
    Возвращает элемент выпадающего списка
    """
    # Ожидаем появления элемента с указанным текстом
    label = wait.until(EC.presence_of_element_located((
        By.XPATH,
        f"//p[normalize-space(.)='{filter_name}']"
    )))
    
    # Находим соответствующий выпадающий список
    select = label.find_element(
        By.XPATH,
        "./ancestor::div[contains(@class,'row')]/div[contains(@class,'col-9')]//mat-select"
    )
    select.click()
    return select

def select_dropdown_option(option_text):
    """Выбор опции в открытом выпадающем списке по тексту"""
    try:
        options = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "app-element-of-hierarchical-list"))
        )
        # Ищем опцию с нужным текстом
        for option in options:
            if option.text.strip() == option_text:
                option.click()
                return
    except Exception as e:
        print(f"Ошибка выбора опции '{option_text}': {e}")

def reset_filters():
    """Сброс всех примененных фильтров"""
    safe_click((
        By.CSS_SELECTOR, "a.citizen-organizations-search-params-clean-filters"
    ))
    time.sleep(0.5)  # Краткая пауза для завершения анимации

def close_dropdown():
    """Закрытие активного выпадающего списка"""
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()

def collect_organizations_data():
    """Основная функция сбора данных об организациях"""
    collected_organizations = []
    while True:
        try:                
            page_source_code = driver.page_source
            soup = BeautifulSoup(page_source_code, "html.parser")
            all_elems = soup.find_all('app-citizen-organizations-list-card')
            
            if len(all_elems) == 0:
                break
            
            for elem in all_elems:
                soup_elem = BeautifulSoup(str(elem), "html.parser")   
                name = soup_elem.select_one('.citizen-organizations-card-title-text a').text.lower()
                # Извлечение ссылки на страницу организации
                details_link = "https://bus.gov.ru" + soup_elem.select_one('.citizen-organizations-card-title-text a')['href']
                # Извлечение ссылки на сайт организации
                try:
                    website_link = soup_elem.select_one('.citizen-organizations-card-website a')['href']
                except:
                    website_link = ""
                    
                collected_organizations.append([name, details_link, website_link])

            # переход на следующую страницу
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, "info-section-paginator__next.ng-star-inserted"))
            ).click()
            
            try:
                # если написано что невозможно отобразить элементы
                WebDriverWait(driver, 1).until(element_has_error_name((By.CLASS_NAME, 'title.title_bold')))
                break
            except:
                continue
                
        except Exception as e:
            break
    
    return collected_organizations

def change_page_size():
    """Изменение количества отображаемых элементов на странице"""
    safe_click((By.CSS_SELECTOR, "mat-select.items-per-page-select"))
    safe_click((By.XPATH, "//span[text()=' 30 ']"))
    
def click_find():
    """Нажать на кнопку 'Найти' внизу формы."""
    btn = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR, "button.citizen-organizations-search-params-filter-button"
    )))
    btn.click()

# Основной поток выполнения
if __name__ == "__main__":
    driver = initialize_driver()
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    collected_data = []

    try:
        driver.get(BASE_URL)
        expand_search_area()

        # Получаем список всех субъектов РФ
        reset_filters()
        open_filter_dropdown("Субъект РФ")
        subjects = [opt.text.strip() for opt in wait.until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "app-element-of-hierarchical-list"))
        )]
        close_dropdown()

        # Обработка каждого субъекта
        for i, subject in enumerate(subjects):
            reset_filters()
            open_filter_dropdown("Субъект РФ")
            select_dropdown_option(subject)
            time.sleep(1.5)  # Ожидание загрузки дочерних элементов
            close_dropdown()

            # Получаем список районов для текущего субъекта
            try:
                open_filter_dropdown("Район/Город")
                time.sleep(1.5)
                regions = [r.text.strip() for r in wait.until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "app-element-of-hierarchical-list"))
                )]
                close_dropdown()
            except:
                # Если районов нет - сохраняем данные и продолжаем
                close_dropdown()
                click_find()
                change_page_size()
                time.sleep(1.5)
                collected_data.extend(collect_organizations_data())
                continue

            # Обработка каждого района
            for j, region in enumerate(regions):
                print(f"Обработка: {subject} -> {region}")
                
                try:
                    open_filter_dropdown("Район/Город")
                    select_dropdown_option(region)
                    time.sleep(1.5)
                    close_dropdown()
                    time.sleep(1)
                    # Запуск поиска и сбор данных
                    click_find()
                    time.sleep(1)  # Ожидание результатов поиска
                    
                    change_page_size()
                    time.sleep(1.5)
                    
                    # Сбор и сохранение данных
                    collected_data.extend(collect_organizations_data())
                    
                except Exception as e:
                    print(f"Ошибка обработки региона {region}: {e}")
                
                try:
                    expand_search_area()
                    open_filter_dropdown("Район/Город")
                    select_dropdown_option(region)
                    time.sleep(1.5)
                    close_dropdown()
                except:
                    pass
                
                # Сохранение промежуточных результатов
                print(f"Собрано организаций: {len(collected_data)}")
                with open(ORGS_STORAGE_FILENAME, 'wb') as f:
                    pickle.dump(collected_data, f)
            
        expand_search_area()
        open_filter_dropdown("Субъект РФ")
        select_dropdown_option(subject)
        time.sleep(1.5)
        close_dropdown()

    finally:
        driver.quit()
        # Финальное сохранение данных
        with open(ORGS_STORAGE_FILENAME, 'wb') as f:
            pickle.dump(collected_data, f)
        print(f"Собрано организаций: {len(collected_data)}")