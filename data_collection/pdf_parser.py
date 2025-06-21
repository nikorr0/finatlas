import pandas as pd
import re
import pdfplumber
from datetime import datetime
from packages.utils import get_indicators
from logger.log_config import logger_print

# загрузка файла с кодами и их названиями, для нахождения их в документе
INDICATORS = get_indicators()
    
MONTH_NUMS = {'январь':"01", 'февраль':"02", 'март':"03", 'апрель':"04", 'май':"05", 'июнь':"06",
            'июль':"07", 'август':"08", 'сентябрь':"09", 'октябрь':"10", 'ноябрь':"11", 'декабрь':"12"}

def get_name_and_year_from_pdf(path=None, page_text=None, return_plan_year=False, return_name=False):
    count = [0]  # Используем список для изменения значения в замыкании

    def replacer(match):
        count[0] += 1
        # Оставляем первое вхождение, остальные заменяем на пустую строку
        return match.group() if count[0] == 1 else ''

    if path is not None:
        with pdfplumber.open(path) as pdf:
            for n_page in range(len(pdf.pages)):
                try:
                    page_text = pdf.pages[n_page].extract_text().lower()
                except:
                    continue
                if "от 17.08.2020 n 168н" in page_text:
                    break
                
    if (page_text is None) and (path is None):
        if not return_plan_year:
            return (None, None)
        if return_plan_year:
            return (None, None, None)
    
    try:
        plan_year_target_text = "план финансово-хозяйственной деятельности на"
        
        page_text = page_text.replace("\n", " ").replace("(сводный)", "")
        plan_year_pattern = r'\s*'.join(map(re.escape, plan_year_target_text))
        plan_year_pattern = re.compile(plan_year_pattern)
        plan_year_search = plan_year_pattern.search(page_text)
        plan_year_span = plan_year_search.span()
        
        plan_year = page_text[plan_year_span[-1]:].replace(" ", "").replace("\n", "")[:4]
        
        if return_name:
            start_pos = re.search(r'(?:ФЕДЕРАЛЬНОЕ|ГОСУДАРСТВЕННОЕ|ГОСУДАРСТВЕННОЕ|ИНСТИТУТ|АКАДЕМИЯ|ОБРАЗОВАТЕЛЬНОЕ|АВТОНОМНОЕ|КАЗЕННОЕ)',
                                                page_text.upper()).start(0)
            
            extracted_name = list(page_text[start_pos:].split("(наименование")[0])
            extracted_name.reverse()
            extracted_name =  '"' + "".join(extracted_name).split('"', maxsplit=1)[-1]
            
            extracted_name = list(extracted_name)
            extracted_name.reverse()
            extracted_name = "".join(extracted_name).replace("\n", " ")
            extracted_name = re.sub(r'\bучреждение\b', replacer, extracted_name)
            extracted_name = re.sub(r'\b[а-яА-я]+\b\s+\d+\b', '', extracted_name)
            extracted_name = re.sub(r'\b\w*\d[\d.]*\w*\b', '', extracted_name)
            extracted_name = re.sub(r'\s+', ' ', extracted_name).strip()
        
        if not return_name:
            extracted_name = None

        date_match = re.search(r'"?(\d+(?:\s+\d+)*)"?\s+([А-Яа-я]+(?:\s+[А-Яа-я]+)*)\s+(\d+(?:\s+\d+)*)\s*г\.?', 
                               page_text, re.IGNORECASE)
        
        day = date_match.group(1).replace(" ", "")
        month = date_match.group(2).lower().replace(" ", "")
        year = date_match.group(3).replace(" ", "")
        
        # Преобразование названия месяца в число
        month_num = MONTH_NUMS.get(month)
        date = f"{day}.{month_num}.{year}"
        if not return_plan_year:
            return (extracted_name, date)
        if return_plan_year:
            return (extracted_name, plan_year, date)
    except:
        if not return_plan_year:
            return (None, None)
        if return_plan_year:
            return (None, None, None)
        

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def to_number(value):
    try:
        return float(value.replace(" ", "").replace(",", "."))
    except ValueError:
        return 0
    
def parse_pdf(names_paths, folder="ПФХД_pdf/"):

    final_dataframe_list = list()
    error_list = list()
    number_of_file = 0

    for org_name, path in names_paths:
        number_of_file += 1
        logger_print(f"Файл №{number_of_file}: {path}")

        try:        
            data_rows = []
            with pdfplumber.open(folder + path) as pdf:
                for n_page in range(len(pdf.pages)):
                    try:
                        page_text = pdf.pages[n_page].extract_text().lower()
                    except:
                        continue
                    # if ("17.08.2020" in page_text) and ("168н" in page_text): (возможное улучшение (не было проверено))
                    if "от 17.08.2020 n 168н" in page_text:
                        break
                
                organization_name = org_name
                _, plan_year, publication_date = get_name_and_year_from_pdf(page_text=page_text, return_plan_year=True)
                
                if (organization_name is None) or (publication_date is None) or (plan_year is None):
                    continue
                
                if plan_year not in list(map(lambda x: str(x), list(range(2022, datetime.now().year + 1)))):
                    continue
                    
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            row = [clean_text(cell) if cell else '' for cell in row]
                            data_rows.append(row)
                
            # Создаем датафрейм из всех строк таблицы PDF
            df = pd.DataFrame(data_rows)

            # загрузка файла с кодами и их названиями, для нахождения их в документе
            data = INDICATORS.copy()

            # Создаем датафрейм из вашего списка
            df_result = pd.DataFrame(
                [f"{code} - {name}" for name, code in data],
                columns=['код - наименование показателя']
            )

            # Добавляем колонку со значениями из таблицы PDF
            values = []
            for name, code in data:
                row = df[df[1].str.contains(code, na=False, case=False, regex=False)]
                values.append(to_number(row.iloc[0, 3]) if not row.empty else 0)

            df_result['Значение'] = values

            
            df_result_transposed = df_result.T
            df_result_transposed.columns = df_result_transposed.iloc[0]  # Первая строка становится заголовком
            df_result_transposed = df_result_transposed[1:]  # Убираем первую строку, так как она теперь заголовок
            df_result_transposed = df_result_transposed.reset_index(drop=True)
            df_result_transposed = df_result_transposed.rename_axis(None, axis=1)
                            
            final_dataframe_list.append([organization_name, plan_year, publication_date] + df_result_transposed.values[0].tolist() + ['pdf'])

                
        except Exception as e:
            logger_print(f"Ошибка при работе с файлом: {path}, ошибка: {e}")
            error_list.append((path, str(e)))
    
    try:
        df_result = pd.DataFrame(final_dataframe_list,
                    columns=['Название организации', 'Год', 'Дата публикации'] + df_result_transposed.columns.to_list() + ['Расширение файла']) 
    
    except:
        logger_print("Новых PDF файлов не найдено")
        return None
    
    df_result = df_result.sort_values(['Название организации', 'Год'], ascending=[True, True])

    return df_result

def create_organization_info_data(university_links):
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
                if col[1] is not None:
                    university_links_data['main_activities'].append(col[1].replace("\n", ", "))
                else:
                    university_links_data['main_activities'].append(None)
            elif col[0] == "Иные виды деятельности по ОКВЭД":
                if col[1] is not None:
                    university_links_data['other_activities'].append(col[1])
                else:
                    university_links_data['other_activities'].append(None)
            elif col[0] == "Адрес фактического местонахождения":
                university_links_data['address'].append(col[1])
            elif col[0] == "Сайт учреждения":
                if (col[1] == "http://") or (col[1] == "https://"):
                    col[1] = None
                if (col[1] is not None) and (col[1][-1] != "/"):
                    col[1] += "/"
                university_links_data['org_link'].append(col[1])
            elif col[0] == "Адрес электронной почты":
                university_links_data['email'].append(col[1])
            elif col[0] == "Широта":
                university_links_data['latitude'].append(col[1])
            elif col[0] == "Долгота":
                university_links_data['longitude'].append(col[1])
    
    return pd.DataFrame(university_links_data)
