import re
import json

def remove_double_spaces_regex(s):
    return re.sub(r' {2,}', ' ', s).strip().lstrip()

def format_organization_name(org_name):
    org_name = remove_double_spaces_regex(org_name)
    if '"' in org_name:
        if org_name.count('"') >= 3:
            formatted_name = org_name.split('"', maxsplit=1)[-1]
        else:
            formatted_name = org_name.split('"')[-2]
    else:
        formatted_name = org_name.split('высшего образования')[-1]
        if "области" in formatted_name:
            formatted_name = formatted_name.split("области")[-1]
    formatted_name = re.sub(r'\s*-\s*', '-', formatted_name).strip().upper()
    return formatted_name

def get_indicators():
    with open('resources/indicators.json', 'r', encoding='utf-8') as file:
        indicators = json.load(file)
    return indicators