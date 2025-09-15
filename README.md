## Языки | Languages
- [Русский](#русский)
- [English](#english)

## Русский
**ФинАтлас**

Проект «ФинАтлас» представляет собой веб-сервис для автоматизации сбора, обработки и визуализации открытых данных о планах финансово-хозяйственной деятельности (ПФХД) высших учебных заведений за отчетные периоды с 2022 года и по настоящее время. Целью проекта является разработка веб-сервиса «ФинАтлас» для сбора, обработки и визуализации открытых данных на примере финансовых потоков вузов. Система собирает данные из государственного реестра (bus.gov.ru) и официальных сайтов вузов, используя эмуляцию действий пользователя, обрабатывает документы в форматах pdf и html, извлекает 69 финансовых показателей и сохраняет их в базу данных. В качестве пользовательского интерфейса реализован сайт с интерактивной картой вузов со страницами с информацией о каждом учреждении из найденных и страницей сравнения финансовых показателей, результаты представляются в виде столбчатых диаграмм. Проект реализован на Python 3.12 с использованием Flask, Selenium и SQLite, охватывает 550 вузов и 1251 документ за отчетные периоды с 2022 года. Область применения: мониторинг финансовой активности образовательных учреждений, внутренний аудит, стратегическое планирование.

---

## Вклад участников

| Участник | Роль в проекте | Ключевой вклад |
|----------|----------------|----------------|
| [**nikorr0**](https://github.com/nikorr0) | Архитектура системы, Backend- и Frontend-разработка | • Проектирование структуры и схемы базы данных<br>• Разработка и внедрение REST API<br>• Реализация интерактивной карты вузов с интеграцией данных<br>• Автоматизация сбора данных с использованием эмуляции пользовательских действий (Selenium)<br>• Обработка и парсинг HTML-документов<br>• Разработка и развертывание веб-приложения на Flask<br>• Контейнеризация проекта |
| [**Sol1tud9**](https://github.com/Sol1tud9) | UI/UX-дизайн, Backend- и Frontend-разработка | • Проектирование и реализация страницы сравнения вузов по финансовым показателям<br>• Разработка интерактивных графиков и диаграмм для визуализации финансовых данных<br>• Обработка и извлечение данных из PDF-документов<br>• Оптимизация пользовательского интерфейса |

---
## Обзор API-эндпоинтов
| Эндпоинт | Описание |
|----------|----------|
| `GET /api/indicators` | Получение кодов и наименований финансовых показателей |
| `GET /api/chart_data` | Получение значений финансовых показателей вузов |
| `GET /api/organizations` | Получение данных о вузах |

---
## Запуск 

Запуск веб-сервиса:
```bash
 flask myrun
```

Запуск веб-сервиса без автоматического сбора данных:
```bash
 flask myrun --skip-data-gathering
```

---

**Карта на начальной странице:**

![](https://github.com/nikorr0/finatlas/blob/main/images/%D0%9A%D0%B0%D1%80%D1%82%D0%B0.png)


**Страница с инфомрацией об организации:**

![](https://github.com/nikorr0/finatlas/blob/main/images/%D0%98%D0%BD%D1%84%D0%BE%D1%80%D0%BC%D0%B0%D1%86%D0%B8%D1%8F_%D0%BE%D0%B1_%D0%BE%D1%80%D0%B3%D0%B0%D0%BD%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D0%B8.png)


**Динамика финансовых показателей на странице с информацией:**

![](https://github.com/nikorr0/finatlas/blob/main/images/%D0%94%D0%B8%D0%BD%D0%B0%D0%BC%D0%B8%D0%BA%D0%B0_%D1%84%D0%B8%D0%BD%D0%B0%D0%BD%D1%81%D0%BE%D0%B2%D1%8B%D1%85_%D0%BF%D0%BE%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D0%B5%D0%BB%D0%B5%D0%B9.png)

**Поле выбора вузов на странице сравнения:**

![](https://github.com/nikorr0/finatlas/blob/main/images/%D0%9E%D0%BA%D0%BD%D0%BE%20%D0%B2%D1%8B%D0%B1%D0%BE%D1%80%D0%B0%20%D0%B2%D1%83%D0%B7%D0%BE%D0%B2.png)

**Сравнение вузов:**

![](https://github.com/nikorr0/finatlas/blob/main/images/%D0%A1%D1%80%D0%B0%D0%B2%D0%BD%D0%B5%D0%BD%D0%B8%D0%B5.png)

**Архитектура проекта в нотации C4:**

![](https://github.com/nikorr0/finatlas/blob/main/images/%D0%90%D1%80%D1%85%D0%B8%D1%82%D0%B5%D0%BA%D1%82%D1%83%D1%80%D0%B0%20%D0%BF%D1%80%D0%BE%D0%B5%D0%BA%D1%82%D0%B0%20C4.png)

**ER-диаграмма базы данных:**

![](https://github.com/nikorr0/finatlas/blob/main/images/ER-%D0%B4%D0%B8%D0%B0%D0%B3%D1%80%D0%B0%D0%BC%D0%BC%D0%B0%20%D0%91%D0%94.drawio.png)

**Блок-схема алгоритма актуализации таблицы планов финансово-хозяйственной деятельности в базе данных:**

<p align="center">
 <img src="https://github.com/nikorr0/finatlas/blob/main/images/%D0%90%D0%BA%D1%82%D1%83%D0%B0%D0%BB%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D1%8F.png" style="width:40%; align-self:center;">
</p>

В соответствии с приказом Минфина РФ № 168н от 17 августа 2020 года государственные и муниципальные учреждения обязаны публиковать планы финансово‑хозяйственной деятельности (ПФХД), при этом в течение года может быть размещено несколько документов. В настоящее время сбор файлов с финансовой отчетностью осуществляется вручную, что требует значительных временных затрат и повышает риск ошибок, связанных с человеческим фактором. Отсутствие единого подхода к публикации ПФХД — размещение на разных сайтах в различных форматах и структурах — дополнительно осложняет централизованный сбор, систематизацию и последующую аналитическую обработку.


## English
**FinAtlas**

The FinAtlas project is a web service designed to automate the collection, processing, and visualization of open data on the Financial and Economic Activity Plans (FEAP) of higher education institutions for reporting periods from 2022 to the present. Its goal is to provide a convenient tool for collecting, processing, and visualizing open data using the example of university financial flows. The system gathers data from the state registry (bus.gov.ru) and official university websites through user action emulation, processes documents in PDF and HTML formats, extracts 69 financial indicators, and stores them in a database. The user interface is implemented as a website featuring an interactive map of universities, individual pages with information on each identified institution, and a comparison page for financial indicators, with results presented as bar charts. The project is built with Python 3.12 using Flask, Selenium, and SQLite, covering 550 universities and 1 251 documents for reporting periods starting from 2022. Its areas of application include monitoring the financial activity of educational institutions, internal audits, and strategic planning.

---

## Contributors

| Participant | Role in the Project | Key Contributions |
|-------------|---------------------|-------------------|
| [**nikorr0**](https://github.com/nikorr0) | System Architecture, Backend and Frontend Development | • Design of the database structure and schema<br>• Development and implementation of the REST API<br>• Implementation of an interactive university map with integrated data<br>• Automation of data collection using user action emulation (Selenium)<br>• Processing and parsing of HTML documents<br>• Development and deployment of the Flask-based web application<br>• Project containerization |
| [**Sol1tud9**](https://github.com/Sol1tud9) | UI/UX Design, Backend and Frontend Development | • Design and implementation of the university comparison page for financial indicators<br>• Development of interactive charts and graphs for financial data visualization<br>• Processing and extraction of data from PDF documents<br>• Optimization of the user interface |

---

## API Endpoints

| Method | Endpoint            | Description |
|--------|---------------------|-------------|
| GET    | `/api/indicators`   | Retrieve the codes and names of financial indicators |
| GET    | `/api/chart_data`   | Retrieve the values of universities’ financial indicators |
| GET    | `/api/organizations`| Retrieve information about organizations |

---
## Getting Started
Run the web service:
```bash
flask myrun
```

Run the web service without automatic data gathering:
```bash
flask myrun --skip-data-gathering
```

---

**Map on the main page:**  

![](https://github.com/nikorr0/finatlas/blob/main/images/%D0%9A%D0%B0%D1%80%D1%82%D0%B0.png)

**Organization information page:**  

![](https://github.com/nikorr0/finatlas/blob/main/images/%D0%98%D0%BD%D1%84%D0%BE%D1%80%D0%BC%D0%B0%D1%86%D0%B8%D1%8F_%D0%BE%D0%B1_%D0%BE%D1%80%D0%B3%D0%B0%D0%BD%D0%B8%D0%B7%D0%B0%D1%86%D0%B8%D0%B8.png)

**Dynamics of financial indicators on the information page:**  

![](https://github.com/nikorr0/finatlas/blob/main/images/%D0%94%D0%B8%D0%BD%D0%B0%D0%BC%D0%B8%D0%BA%D0%B0_%D1%84%D0%B8%D0%BD%D0%B0%D0%BD%D1%81%D0%BE%D0%B2%D1%8B%D1%85_%D0%BF%D0%BE%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D0%B5%D0%BB%D0%B5%D0%B9.png)

**University selection field on the comparison page:**  

![](https://github.com/nikorr0/finatlas/blob/main/images/%D0%9E%D0%BA%D0%BD%D0%BE%20%D0%B2%D1%8B%D0%B1%D0%BE%D1%80%D0%B0%20%D0%B2%D1%83%D0%B7%D0%BE%D0%B2.png)

**University comparison:**  

![](https://github.com/nikorr0/finatlas/blob/main/images/%D0%A1%D1%80%D0%B0%D0%B2%D0%BD%D0%B5%D0%BD%D0%B8%D0%B5.png)

**Project architecture in C4 notation:**  
![](https://github.com/nikorr0/finatlas/blob/main/images/Project_architecture_C4.png)


**ER diagram of the database:**  
![](https://github.com/nikorr0/finatlas/blob/main/images/ER_diagram_of_the_database.png)


**Flowchart of the algorithm for updating the table of financial and economic activity plans in the database:**  

<p align="center">
 <img src="https://github.com/nikorr0/finatlas/blob/main/images/Actualization.png" style="width:40%; align-self:center;">
</p>

In accordance with Order No. 168n of the Ministry of Finance of the Russian Federation dated August 17, 2020, state and municipal institutions are required to publish financial and economic activity plans (FEAP), with multiple documents potentially issued within a single year. Currently, financial reporting files are collected manually, which is time‑consuming and increases the risk of human error. The lack of a unified approach to publishing FEAPs—spread across various websites in different formats and structures—further complicates centralized collection, organization, and subsequent analysis.
