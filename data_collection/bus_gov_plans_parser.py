import pandas as pd
from packages.utils import get_indicators
from bs4 import BeautifulSoup
from datetime import datetime

INDICATORS = get_indicators()

def parse_financial_data_html(html_file_path, year_from_filename=True):
    """
    Парсит финансовые данные из HTML файла
    Возвращает список из элементов:
    [название организации, год, дата публикации, значение1, значение2, ...]
    """    
    # Парсим HTML
    with open(html_file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')

    try:
        # Извлекаем название организации (первый элемент)
        org_name = soup.find('td', string='Учреждение')
        org_name = org_name.find_next_sibling('td').get_text(strip=True).lower()
    except:
        org_name = None
    
    if not year_from_filename:
        year = None
        try:
            # Извлекаем год (второй элемент)
            h2_text = soup.find('h2').get_text().split("г.")[0]
            
            for year_int in range(2022, datetime.now().year + 1):
                if f'{year_int}' in h2_text:
                    year = f'{year_int}'
        except:
            pass
    else:
        year = html_file_path.split("_")[-1].replace(".html", "")
    
    try:
        publication_date = soup.find('date').get_text(strip=True)
    except:
        publication_date = None
    
    # Находим таблицу с данными
    try:
        section = soup.find('h3', string='Раздел 1. Поступления и выплаты')
        table = section.find_next('table') if section else None
        rows = table.find_all('tr') if table else []
        all_columns = table.find_all('th')
        
        values_col_ind = 0
        for col in all_columns:
            if "Сумма" in str(col):
                break 
            values_col_ind += 1
        
        code_col_ind = 0
        for col in all_columns:
            if "Код" in str(col):
                break 
            code_col_ind += 1
            
        # Создаем словарь {код: значение} для быстрого поиска
        data_dict = {}
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4:  # Проверяем наличие нужных столбцов
                code = cells[code_col_ind].get_text(strip=True)
                value = cells[values_col_ind].get_text(strip=True)  # Столбец "текущий финансовый год"
                
                if code:  # Если есть код показателя
                    try:
                        data_dict[code] = float(value.replace(' ', '').replace(',', '.'))
                    except (ValueError, AttributeError):
                        data_dict[code] = 0.0

        # Формируем итоговый список
        result = [org_name, year, publication_date] 
        
        # Добавляем значения по порядку индикаторов
        for _, code in INDICATORS:
            result.append(data_dict.get(code, 0.0))
    except:
        result = [org_name, year, publication_date] + [None] * len(INDICATORS)
        
    return result + ['html']

# Пример использования:
# parse_financial_data_html("ПФХД_html/test/Тюменский_государственный_университет_2022.html", indicators_pickle_path=None, year_from_filename=False)
# if __name__ == "__main__":
#     data = parse_financial_data_html(
#         r'c:\Users\Honor\Desktop\Project University finance\Организация2.html',
#         r'c:\Users\Honor\Desktop\Project University finance\indicators.pickle'
#     )
#     logger_print(f"Получено данных: {len(data)}")
#     logger_print(f"Год: {data[1]}")
#     logger_print(f"Первые 5 значений: {data[2:]}")

# for universities_plans_data
# parse_financial_data_html("ПФХД_html/gov/" + html_file_path, indicators_pickle_path=None)

# logger_print(f"Получено данных: {len(data)}")
# logger_print(f"Год: {data[1]}")


def create_organization_plans_data(plans_list):
    column_names = ["Название организации", "Год", "Дата публикации"] \
        + list(map(lambda x: f"{x[1]} - {x[0]}", INDICATORS)) + ["Расширение файла"]
    
    organization_plans_data = pd.DataFrame(plans_list, 
                            columns=column_names)    
    
    return organization_plans_data