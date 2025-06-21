import pandas as pd
import sqlite3
from datetime import datetime
from .utils import get_indicators

INDICATORS = get_indicators()

DATABASE_PATH = 'resources/organization_database.db'

def get_tables(purpose='site'):
    with sqlite3.connect(DATABASE_PATH) as conn:
        indicator_fields = ", ".join(f"opd.code_{code}" for code in INDICATORS.keys())

        plan_query = f"""
            SELECT on2.formatted_name, opd.plan_year as year, 
            opd.publication_date as publication_date, {indicator_fields}
            FROM organization_plans opd
            JOIN org_name on2 ON opd.org_name_id = on2.id;
        """
        data_plan_year = pd.read_sql_query(plan_query, conn).fillna("Информация не найдена")

        info_query = """
            SELECT oi.id, on2.formatted_name, oi.gov_link, ot.type_name, ok.kind_name,
                oi.main_activities, oi.address, oi.email, oi.org_link, oi.latitude, oi.longitude
            FROM organization_info oi
            JOIN org_name on2 ON oi.org_name_id = on2.id
            JOIN org_type ot ON oi.org_type_id = ot.id
            JOIN org_kind ok ON oi.org_kind_id = ok.id;
        """
        data_org_info = pd.read_sql_query(info_query, conn).fillna("Информация не найдена")
    
    # удаление строк, где слишком много нулевых значений (скорее всего неверно спарсилось)
    zero_ratio = data_plan_year.eq(0).mean(axis=1)
    data_plan_year = data_plan_year.loc[zero_ratio <= 0.97].copy()
    
    # удаление строк с неправильной датой публикации (скорее всего неверно спарсилось)
    data_plan_year['publication_date_parsed'] = pd.to_datetime(
        data_plan_year['publication_date'],
        format='%d.%m.%Y',
        errors='coerce'
    )
    # Оставим только те строки, где парсинг удался
    data_plan_year = data_plan_year.dropna(subset=['publication_date_parsed'])
    data_plan_year = data_plan_year.drop(columns=['publication_date_parsed'])
    
    data_plan_year = data_plan_year.reset_index(drop=True)
    
    if purpose == 'site':
        data_plan_year = data_plan_year.drop(columns=['publication_date'])
    
    return data_org_info, data_plan_year

def upsert_organization_plan(formatted_name, plan_year, publication_date, indicator_values, DATE_FMT="%d.%m.%Y"):
    """
    Обновляет или вставляет строку в таблице organization_plans по ключу:
    (formatted_name, plan_year, publication_date). 
    
    Если запись существует, то она обновляется. 
    Если не найдена — вставляется новая.
    
    Параметры:
        formatted_name (str): отформатированное имя организации (поле org_name.formatted_name).
        plan_year (int): год плана.
        publication_date (str): дата публикации в формате 'DD-MM-YYYY'.
        indicator_values (dict): словарь вида {'code_0001': value1, 'code_0002': value2, ...}.
                                 Ключи здесь — именно имена столбцов в таблице organization_plans.
    """
    if not indicator_values:
        print("Словарь indicator_values пуст. Нет полей для обновления.")
        return False

    new_date = datetime.strptime(publication_date, DATE_FMT).date()

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cur = conn.cursor()

            # 1. id организации
            cur.execute("SELECT id FROM org_name WHERE formatted_name = ?",
                        (formatted_name,))
            row = cur.fetchone()
            if not row:
                print(f"Организация '{formatted_name}' не найдена.")
                return False
            org_name_id = row[0]

            # 2. самая свежая дата, уже лежащая в БД, для (org_name_id, plan_year)
            cur.execute("""
                SELECT rowid,
                    publication_date
                FROM   organization_plans
                WHERE  org_name_id = ? AND plan_year = ?

                ORDER  BY
                    substr(publication_date, 7, 4)  ||  -- YYYY
                    substr(publication_date, 4, 2)  ||  -- MM
                    substr(publication_date, 1, 2)       -- DD
                    DESC
                LIMIT  1;
            """, (org_name_id, plan_year))

            existing = cur.fetchone()

            if existing:
                rowid_db, date_db_str = existing
                date_db = datetime.strptime(date_db_str, DATE_FMT).date()

                # Если в базе дата ≥ новой => выход
                if date_db >= new_date:
                    print("В БД уже есть строка с такой же или более новой датой."
                          " Обновление не требуется.")
                    return True

                # Иначе обновляем существующую строку
                set_clause = ", ".join(f"{col} = ?" for col in indicator_values)
                params = list(indicator_values.values()) + [
                    publication_date,         # новая дата
                    rowid_db                  # WHERE rowid = ?
                ]
                update_sql = f"""
                    UPDATE organization_plans
                    SET {set_clause},
                        publication_date = ?
                    WHERE rowid = ?;
                """
                cur.execute(update_sql, params)
                conn.commit()
                print("Запись обновлена (дата стала новее).")
                return True

            # 3. Записи ещё не было — вставляем новую
            insert_cols = ["org_name_id", "plan_year", "publication_date"]
            insert_vals = [org_name_id, plan_year, publication_date]
            insert_cols += list(indicator_values.keys())
            insert_vals += list(indicator_values.values())

            placeholders = ", ".join("?" for _ in insert_cols)
            cur.execute(f"""
                INSERT INTO organization_plans ({", ".join(insert_cols)})
                VALUES ({placeholders});
            """, insert_vals)
            conn.commit()
            print("Новая строка добавлена.")
            return True

    except Exception as e:
        print("Ошибка при работе с organization_plans:", e)
        return False
