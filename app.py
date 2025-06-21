from flask import Flask, render_template, jsonify, send_file
from flask_apscheduler import APScheduler
import click
from flask.cli import with_appcontext
from datetime import datetime
import pandas as pd
import io
import os
import subprocess
import platform
import argparse
import sys
from packages.utils import get_indicators
from packages.database_utils import get_tables
from data_collection.data_gathering_pipeline import main_process
from logger.log_config import get_logger, logger_print
from logger.logging_routes import bp as log_bp 

# создание папки "resources/ПФХД_html/" 
# и "resources/ПФХД_pdf/" если их нет
os.makedirs(os.path.join('resources', 'ПФХД_html'), 
            exist_ok=True)
os.makedirs(os.path.join('resources', 'ПФХД_pdf'),  
            exist_ok=True)

def element_to_dict_organization(row):
    columns = [
        'id', 'name', 'gov_link', 'institution_type', 
        'institution_kind', 'main_activities', 
        'address', 'email', 'website', 'latitude', 'longitude'
    ]
    return {col: val for col, val in zip(columns, row)}

def element_to_dict_plan(row, indicators):
    """Преобразование строки данных в словарь"""
    result = dict()
    for val, key in zip(row, indicators):
        if key == 'year':
            val = int(val)
        if key not in ['name', 'year']:
            key = f"code_{key}"
        result[key] = val
    return result

def find_index_to_drop(df):
    index_to_drop = list()
    for org_name in df['formatted_name'].unique():
        year = list()
        indices = list(df[df['formatted_name'] == org_name]['year'].index)
        indices.reverse()
        for i in indices:
            year_ind = df['year'].iloc[i]
            if year_ind not in year:
                year.append(year_ind)
            else:
                index_to_drop.append(i)
    return index_to_drop

def refresh_data():
    """Читаем БД и пересобираем global-переменные."""
    global indicators, organizations, chart_data

    # Загрузка названий столбцов ПФХД
    # в формате списка пар ["Название", "0001"]
    indicators = get_indicators()
    
    # Загрузка данных из базы данных
    data_org_info, data_plan_year = get_tables()

    data_plan_year = data_plan_year.drop(find_index_to_drop(data_plan_year), axis=0)

    organizations = sorted(
        [element_to_dict_organization(r) for r in data_org_info.to_numpy()],
        key=lambda x: x['name']
    )

    chart_data = [
        element_to_dict_plan(
            r,
            ['name', 'year'] + [code for code in indicators.keys()]
        ) for r in data_plan_year.to_numpy()
    ]

# Подгружаем данные из базы данных
refresh_data()

# Flask приложение
class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_EXECUTORS = {
        "default": {
            "type": "threadpool", 
            "max_workers": 1
            }
        }

app = Flask(__name__) 
app.config["SKIP_DATA_GATHERING"] = (
    os.getenv("SKIP_DATA_GATHERING", "0").lower() in ("1", "true", "yes")
)

app.register_blueprint(log_bp)
logger = get_logger()

app.config.from_object(Config())

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

now = datetime.now()

if now.minute == 59:
    minute = 0
    hour = now.hour + 1
else:
    minute = now.minute + 1
    hour = now.hour 
    
@scheduler.task('cron',
                id='data_gathering',
                month='*',
                day=str(now.day),
                hour=str(hour),
                minute=str(minute), 
                max_instances=1, 
                coalesce=True)
def data_gathering():
    if app.config.get("SKIP_DATA_GATHERING", False):
        logger_print("ПРЕДУПРЕЖДЕНИЕ: Сбор данных отключен")
        return
    # Начинаем сбор данных и обновление базы данных
    main_process()
    # Обновляем глобальные переменные (чтобы обновить данные на страницах /api/)
    refresh_data()

@app.route("/healthz")
def healthz():
    return "OK", 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/indicators')
def get_indicators_json():
    return jsonify(indicators)

@app.route('/university-details')
def university_details():
    return render_template('university-details.html')

@app.route('/comparison')
def comparison():
    return render_template('comparison.html')

@app.route('/logging')
def logging ():
    return render_template('logging.html')

@app.route('/api/organizations')
def get_organizations():
    return jsonify(organizations)

@app.route('/api/chart_data')
def get_chart_data():
    return jsonify(chart_data)

@app.route('/download-excel')
def download_excel():
    org_headers = [
        'Название ВУЗа', "Ссылка на гос. реестр", "Тип ВУЗа", "Вид ВУЗа",
        "Основные виды деятельности по ОКВЭД", 'Адрес', 'Email', 
        'Сайт организации', 'Широта', 'Долгота'
    ]
    plan_headers = ['Название ВУЗа', 'Год'] + [f"{code} - {desc}" for code, desc in indicators.items()]
    
    org_df = pd.DataFrame(organizations).drop(columns=['id'])
    org_df.columns = org_headers

    plan_df = pd.DataFrame(chart_data)
    plan_df.columns = plan_headers
    
    # Сортируем сначала по названию вуза, затем по году
    plan_df.sort_values(by=['Название ВУЗа', 'Год'], inplace=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        org_df.to_excel(writer, sheet_name='Организации', index=False)
        plan_df.to_excel(writer, sheet_name='Финансовые показатели', index=False)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='FinAtlas_Data.xlsx'
    )

@app.cli.command("myrun")
@click.option("--skip-data-gathering", is_flag=True, help="Используйте --skip-data-gathering чтобы запустить сервер без выполнения планового задания data_gathering().")
@with_appcontext
def myrun(skip_data_gathering):
    if skip_data_gathering:
        os.environ["SKIP_DATA_GATHERING"] = "1"
    else:
        os.environ["SKIP_DATA_GATHERING"] = "0"
        
    env_default = os.getenv("SKIP_DATA_GATHERING", "0")
    app.config["SKIP_DATA_GATHERING"] = env_default

    os_name = platform.system()
    
    if os_name == "Windows": 
        from werkzeug.serving import run_simple
        run_simple("0.0.0.0", 10000, app, threaded=True)
    
    else:
        if app.config.get("SKIP_DATA_GATHERING", False):
            cmd = ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
        else:
            cmd = ["gunicorn", "-w", "4", "-b", "0.0.0.0:10000", "app:app"]
            
        subprocess.run(cmd, check=True, env=os.environ.copy())