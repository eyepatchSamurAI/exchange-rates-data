from xml.dom.minidom import Element
import requests
import xml.etree.ElementTree as ET
import json

DATA_FOLDER = "data"

def read_json_file(path: str):
    with open(path, "r") as f:
        return json.load(f)

def write_json_file(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    
def get_country_data():
    return read_json_file(f"{DATA_FOLDER}/countries.json")


def get_daily_exchange_rate_xml():
    url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
    response = requests.get(url)
    response.raise_for_status()
    return ET.fromstring(response.content)


def get_exchange_rates_from_xml_element(root: Element):
    namespaces = {
        'gesmes': 'http://www.gesmes.org/xml/2002-08-01',
        '': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'
    }

    time_element = root.find(".//Cube[@time]", namespaces)
    timestamp = time_element.get('time') if time_element is not None else None
    exchange_rates = {}

    for cube in time_element.findall("Cube", namespaces):
        currency = cube.get('currency')
        rate = cube.get('rate')
        if currency and rate:
            exchange_rates[currency] = float(rate)
    return {
        "timestamp": timestamp,
        "exchange_rates": exchange_rates
    }

def merge_country_and_currency_data(country_data, exchange_rates_data):
    merged_data = {
        "EUR": {
            "country_name": "European Union",
            "currency_name": "Euro",
            "currency_iso_code": "EUR",
            "alpha2_code": "EU",
            "numeric_id": 978,
            "exchange_rate": 1.0,
            "country_code": "EU" # Only one with a three digit country code
        }

    }
    for country_code, details in country_data.items():
        currency_code = details.get("currency_iso_code")
        exchange_rates = exchange_rates_data.get("exchange_rates", {})
        if currency_code in exchange_rates:
            details["exchange_rate"] = exchange_rates[currency_code]
            details["country_code"] = country_code
            merged_data[currency_code] = details

    return {
        "timestamp": exchange_rates_data["timestamp"],
        "currencies": merged_data
    }

if __name__ == "__main__":
    current_exchange_rates = read_json_file(f"./{DATA_FOLDER}/exchange_rates.json")
    country_data = get_country_data()
    eu_exchange_rates = get_daily_exchange_rate_xml()
    exchange_rates_data = get_exchange_rates_from_xml_element(eu_exchange_rates)
    result = merge_country_and_currency_data(country_data, exchange_rates_data)
    # Update Previous exchange_rates
    write_json_file(f"./{DATA_FOLDER}/prev_exchange_rates.json", current_exchange_rates)
