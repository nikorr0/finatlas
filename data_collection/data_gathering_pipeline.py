import time
import os
import shutil
from datetime import datetime
import requests
from urllib.parse import urljoin
from packages.utils import get_indicators
from packages.database_utils import get_tables, upsert_organization_plan
from data_collection.pdf_downloader import download_correct_file, check_file_readability
from data_collection.pdf_parser import parse_pdf
from data_collection.utils import get_header
from data_collection.pdf_parser import get_name_and_year_from_pdf
from data_collection.bus_gov_plans_downloader import download_html_tables_from_url
from data_collection.bus_gov_plans_parser import parse_financial_data_html
from logger.log_config import logger_print

FOLDER_TO_SAVE_PDF = "resources/ПФХД_pdf/"
FOLDER_TO_SAVE_HTML = "resources/ПФХД_html/"

def update_processed_orgs(processed_orgs, current_name_date_filename, folder_to_save):
    if len(processed_orgs) == 0:
        processed_orgs.append(current_name_date_filename)
    else:
        org_names = list(map(lambda x: x[0], processed_orgs))
        if current_name_date_filename[0] not in org_names:
            processed_orgs.append(current_name_date_filename)
        else:
            current_org_name = current_name_date_filename[0]
            current_year = current_name_date_filename[1]
            current_date_str = current_name_date_filename[2]
            existing_entries = [entry for entry in processed_orgs if entry[0] == current_org_name]
            year_exists = False
            for entry in existing_entries:
                entry_year = entry[1]
                
                # Сравниваем годы
                if entry_year == current_year:
                    year_exists = True
                    current_date = datetime.strptime(current_date_str, "%d.%m.%Y")
                    entry_date = datetime.strptime(entry[2], "%d.%m.%Y")
                    
                    # Сравниваем даты
                    if current_date > entry_date:
                        # Удаляем старый файл
                        logger_print(f"Удаляем старые данные: {entry[-1]}")
                        if current_name_date_filename[-1] != 'Из базы данных':
                            old_file_path = os.path.join(folder_to_save, entry[-1])
                            if os.path.exists(old_file_path):
                                os.remove(old_file_path)
                        # Удаляем старую запись из списка
                        processed_orgs.remove(entry)
                        # Добавляем новую запись
                        processed_orgs.append(current_name_date_filename)
                    else:
                        # Удаляем новый файл
                        logger_print(f"Удаляем новые данные: {current_name_date_filename[-1]}")
                        if current_name_date_filename[-1] != 'Из базы данных':
                            new_file_path = os.path.join(folder_to_save, current_name_date_filename[-1])
                            if os.path.exists(new_file_path):
                                os.remove(new_file_path)
                        
                    break  # Прерываем цикл после обработки

            # Если года нет в существующих записях, добавляем новую запись
            if not year_exists:
                processed_orgs.append(current_name_date_filename)
    
    return processed_orgs

def get_allowed_years(present_years):
    allowed_years = list(set(map(lambda x: str(x), [x for x in range(2022, datetime.now().year + 1)])) - set(present_years))
    
    current_year = str(datetime.now().year)
    if current_year not in allowed_years:
        allowed_years.append(current_year)
        logger_print(f"Добавляем текущий год ({current_year}) в список недостающих, чтобы найти более актуальный файл ПФХД")
    
    return sorted(allowed_years)

def get_processed_orgs(data_plan_year):
    processed_orgs = list()
    
    filtered_data = data_plan_year[data_plan_year['year'] == str(datetime.now().year)]
    filtered_data = filtered_data[['formatted_name', 'publication_date', 'year']].values
    for values in filtered_data:
        processed_orgs.append(list(values) + ['Из базы данных'])
        
    return processed_orgs
        
def gather_plans_data_html():
    # Загрузка данных из базы
    data_org_info, data_plan_year = get_tables(purpose='gathering')
    # Перемешиваем данные 
    data_org_info = data_org_info.sample(frac=1).reset_index(drop=True)
    # Сбор HTML файлов с государственного реестра bus.gov.ru 
    processed_orgs = get_processed_orgs(data_plan_year)
    
    start_time = time.time()
    
    logger_print("Начинается выполнение поиска, загрузки и обработки HTML файлов ПФХД с государственного реестра...")
    # ВНИМАНИЕ: на сайте bus.gov.ru есть ограничения. После 700 запросов сайт запрещает доступ к данным на некоторое время.
    # Через 1-2 часа, когда сайт снимет ограничение на доступ с IP адреса, можно продолжать.
    quota = 700
    num_university = 0
    
    for org_name, url in data_org_info[['formatted_name', 'gov_link']].values:
        num_university += 1
        
        if url[len(url) - 6:] != "/plans":
            if url[-1] != "/":
                url += "/"
            url += "plans"
            
        logger_print(f"№{num_university} {org_name}")
        logger_print(f"Ссылка на сайт с ПФХД: {url}")
        present_years = list(data_plan_year[data_plan_year["formatted_name"] == org_name]['year'].values)
        allowed_years = get_allowed_years(present_years)
        logger_print(f"Список недостающих годов: {allowed_years}")
        try:
            universities_plans_data = download_html_tables_from_url(url=url, org_name=org_name, 
                                                                    years_to_parse=allowed_years,
                                                                    save_to=FOLDER_TO_SAVE_HTML)
            
            # Проверка и обновление квоты
            required_quota = 2 * len(allowed_years)
            if quota < required_quota:
                logger_print("ПРЕДУПРЕЖДЕНИЕ: Превышена квота на запросы к bus.gov.ru, ожидаем 2 часа")
                time.sleep(3600*2)
                quota = 700  # Сброс квоты после ожидания
            
            quota -= required_quota
            
            universities_plans_list = zip(universities_plans_data['plan_year'].values, 
                                          universities_plans_data['plan_filename'].values)
        except Exception as e:
            logger_print(f"Ошибка скачивания HTML файлов с {url}. Ошибка: {e}")
            continue
        for plan_year, filename in universities_plans_list:
            logger_print(f"Найден файл за {plan_year} год: {filename}")
            full_financial_list = parse_financial_data_html(FOLDER_TO_SAVE_HTML + filename)
            full_financial_list[0] = org_name
            processed_orgs = update_processed_orgs(processed_orgs, full_financial_list + [filename], FOLDER_TO_SAVE_HTML)
            
    redacted_processed_orgs = list()
    for values in processed_orgs:
        if values [-1] != "Из базы данных":
            redacted_processed_orgs.append(values[:len(values)-1])
    
    logger_print(f"Время затраченное на поиск, загрузку и обработку HTML файлов ПФХД с государственного реестра: {round(time.time() - start_time, 2)} сек.")
    logger_print(f"Обработано вузов: {num_university}")
    logger_print(f"Количество новых/измененных записей: {len(redacted_processed_orgs)}")
            
    return redacted_processed_orgs

def gather_plans_data_pdf():
    # Загрузка данных из базы
    data_org_info, data_plan_year = get_tables(purpose='gathering')
    data_org_info = data_org_info[data_org_info['org_link'] != "Информация не найдена"]
    # Перемешиваем данные 
    data_org_info = data_org_info.sample(frac=1).reset_index(drop=True)
    # Сбор PDF файлов с официальных сайтов вузов 
    HEADERS = get_header()
    processed_orgs = get_processed_orgs(data_plan_year)
    
    num_university = 0
    start_time = time.time()

    logger_print("Начинается выполнение поиска и загрузки PDF файлов ПФХД с официальных сайтов вузов...")
    # Вместо столбца 'org_link' можно использовать 'plan_link', 
    # но в данный момент он пустой, этот столбец предусмотрен для 
    # хранения ссылок вуза, на которых содержатся PDF файлы ПФХД
    for name, org_link in data_org_info[['formatted_name', 'org_link']].values:
        name = name.replace('"', "'")
        
        num_university += 1
        logger_print(f"№{num_university} {name}")
        
        if not org_link:
            continue
        
        url = urljoin(org_link, '/sveden/budget')
        logger_print(f"Ссылка на сайт с ПФХД: {url}")

        present_years = list(data_plan_year[data_plan_year["formatted_name"] == name]['year'].values)
        allowed_years = get_allowed_years(present_years)
        logger_print(f"Список недостающих годов: {allowed_years}")
        
        pdf_links_checked = list()
        
        pdf_links = download_correct_file(url, allowed_years=allowed_years)
        if pdf_links:
            for pdf_link in pdf_links:
                readable = check_file_readability(pdf_link, allowed_years=allowed_years)
                logger_print(f"Найден файл: {pdf_link} (Читабельный: {readable})")
                if readable:
                    pdf_links_checked.append(pdf_link)
        
        if not pdf_links:
            logger_print("Подходящие файлы не найдены")
        
        for pdf_link in pdf_links_checked:
            response = requests.get(pdf_link, headers=HEADERS, timeout=10)
            response.raise_for_status()
            filename = f"{name}_{str(round(time.time(), 2))}.pdf"
            with open(FOLDER_TO_SAVE_PDF + filename, 'wb') as f:
                f.write(response.content)
            
            try:
                name_date_filename = list(get_name_and_year_from_pdf(FOLDER_TO_SAVE_PDF + filename, return_plan_year=True)) + [filename]
                name_date_filename[0] = name
                
                processed_orgs = update_processed_orgs(processed_orgs, name_date_filename, FOLDER_TO_SAVE_PDF)
            except Exception as e:
                logger_print(f"ОШИБКА: {e}")
                continue
    
    redacted_processed_orgs = list()
    for values in processed_orgs:
        if values [-1] != "Из базы данных":
            redacted_processed_orgs.append([values[0], values[-1]])

    logger_print(f"Время затраченное на поиск и загрузку PDF файлов ПФХД с официальных сайтов вузов: {round(time.time() - start_time, 2)} сек.")
    logger_print(f"Обработано вузов: {num_university}")

    logger_print("Начинается выполнение парсинга загруженных PDF файлов...")
    start_time = time.time()
    plans_data_pdf = parse_pdf(redacted_processed_orgs, folder=FOLDER_TO_SAVE_PDF)
    end_time = time.time() - start_time
    logger_print(f"Время затраченное на парсинг: {round(end_time, 2)} сек.")
    logger_print(f"Количество новых/измененных записей: {len(redacted_processed_orgs)}")
    
    if plans_data_pdf is not None:
        logger_print(f"Среднее время парсинга одного файла: {round(end_time / plans_data_pdf.shape[0], 2)}")
        return plans_data_pdf.values
    else:
        return None

def update_database(processed_orgs):
    if processed_orgs is None:
        logger_print("База данных не была обновлена, так как нет данных для обновления.")
        return
    
    try:
        indicators = get_indicators()
        indicator_fields = [f"code_{code}" for _, code in indicators] + ['file_extension']

        statuses = list()
        for values in processed_orgs:
            values = list(values)
            org_name = values.pop(0)
            plan_year = values.pop(0)
            publication_date = values.pop(0)
            
            indicator_values = dict()
            for i, indicator_field in enumerate(indicator_fields):
                indicator_values[indicator_field] = values[i]
                
            status = upsert_organization_plan(org_name, plan_year, publication_date, indicator_values)
            statuses.append(status)
        if not False in statuses:
            logger_print("База данных успешно обновлена")
        else:
            logger_print("Ошибка: База данных не была обновлена")
    except Exception as e:
        logger_print(f"Ошибка обновления базы данных: {e}")

def clear_directory(folder):
    logger_print(f"Очистка содержимого папки {folder}")
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger_print(f"Ошибка: Не удалось удалить файлы в папке {folder}, {e}")

def main_process():

    start_time = time.time()
    
    processed_orgs_html = gather_plans_data_html()
    
    update_database(processed_orgs_html)
    
    processed_orgs_pdf = gather_plans_data_pdf()
    
    update_database(processed_orgs_pdf)
    
    clear_directory(FOLDER_TO_SAVE_HTML)
    clear_directory(FOLDER_TO_SAVE_PDF)
    
    logger_print("Сбор данных успешно завершен")
    logger_print(f"Общее время выполнения: {round(time.time() - start_time, 2)} сек.")
    
    