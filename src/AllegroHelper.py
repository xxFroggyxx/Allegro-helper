import datetime
import json
import os
import time
from collections import OrderedDict

import requests
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CODE_URL = "https://allegro.pl/auth/oauth/device"
TOKEN_URL = "https://allegro.pl/auth/oauth/token"


def get_code():
    """Returns the necessary device_code that you will need to obtain access_token"""
    try:
        payload = {'client_id': CLIENT_ID}
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        api_call_response = requests.post(CODE_URL, auth=(CLIENT_ID, CLIENT_SECRET),
                                          headers=headers, data=payload, verify=True)
        return api_call_response
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def get_access_token(device_code: str):
    """
    Returns access_token to communicate with API.

      device_code: str
        necessary code for proper work.
    """
    try:
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        data = {'grant_type': 'urn:ietf:params:oauth:grant-type:device_code', 'device_code': device_code}
        api_call_response = requests.post(TOKEN_URL, auth=(CLIENT_ID, CLIENT_SECRET),
                                          headers=headers, data=data, verify=True)
        return api_call_response
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def await_for_access_token(interval: int, device_code: str):
    """
    Returns or saves essential access_token to communicate with API and do responses with user recognition. With using get_access_token.

      interval: int
        do interval as it names.
      device_code: str
        necessary code for proper work.
    """
    while True:
        time.sleep(interval)
        result_access_token = get_access_token(device_code)
        token = json.loads(result_access_token.text)
        if result_access_token.status_code == 400:
            if token['error'] == 'slow_down':
                interval += interval
            if token['error'] == 'access_denied':
                break
        else:
            now = datetime.datetime.now()
            expire_time = now + datetime.timedelta(seconds=43199)
            with open("expiring.txt", "w") as f:
                f.write(f"EXPIRE_TIME>>>{expire_time.strftime('%Y-%m-%d %H:%M:%S')}\nACCESS_TOKEN>>>{token['access_token']}")

            return token['access_token']


def get_all_orders(token: str):
    """
    Returns last 100 orders.

      token: str
        access token which enables to do queries.
    """
    try:
        url = "https://api.allegro.pl/order/checkout-forms"
        headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        all_orders_result = requests.get(url, headers=headers, verify=True)
        return all_orders_result.json()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def get_orders(token: str):
    """
    Returns the last 100 orders which payment is done and are ready to ship/shipped.

      token: str
        access token which enables to do queries.
    """
    try:
        url = "https://api.allegro.pl/order/checkout-forms?status=READY_FOR_PROCESSING&fulfillment.status=SENT&fulfillment.status=READY_FOR_SHIPMENT"
        headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        orders_result = requests.get(url, headers=headers, verify=True)
        return orders_result.json()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def get_orders_with_date_border(token: str, date: str, sort: str = "Descending"):
    """
    Returns sorted ordered items, with the required date option to enter the day from which day to count until today.

      date: str
        you enter the date that will be the end condition of this method.
      sort: str ***OPTIONAL***
        by default Descending. Choose from three sorting methods.
          Alphabetical: Alphabetical, alphabetical, alph
          Ascending: Ascending, ascending, asc
          Descending: Descending, descending, desc
    """
    givenDate = datetime.datetime.strptime(date, "%Y-%m-%d")
    print(f"Wszystkie przedmioty sprzedane do {givenDate.date()} włącznie:")
    n = 0
    count_products = {}
    while True:
        try:
            url = f"https://api.allegro.pl/order/checkout-forms?status=READY_FOR_PROCESSING&fulfillment.status=SENT&fulfillment.status=READY_FOR_SHIPMENT&offset={n}"
            headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
            orders_date_result = requests.get(url, headers=headers, verify=True).json()

            for ind in range(len(orders_date_result["checkoutForms"])):
                productBoughtDate = datetime.datetime.strptime(orders_date_result["checkoutForms"][ind]["lineItems"][0]["boughtAt"][0:10], "%Y-%m-%d")

                if givenDate > productBoughtDate:
                    if sort in ["Alphabetical", "alphabetical", "alph"]:
                        return OrderedDict(sorted(count_products.items(), key=lambda item: item[0]))
                    elif sort in ["Ascending", "ascending", "asc"]:
                        return OrderedDict(sorted(count_products.items(), key=lambda item: (item[1], item[0])))
                    elif sort in ["Descending", "descending", "desc"]:
                        return OrderedDict(sorted(count_products.items(), key=lambda item: (item[1], item[0]), reverse=True))
                    else:
                        print("Popraw opcje sortu! Dostępne: alphabetical, ascending, descending")
                        return

                for x in range(len(orders_date_result["checkoutForms"][ind]["lineItems"])):
                    if not orders_date_result["checkoutForms"][ind]["lineItems"][x]["offer"]["name"] in count_products:
                        count_products[orders_date_result["checkoutForms"][ind]["lineItems"][x]["offer"]["name"]] = \
                            orders_date_result["checkoutForms"][ind]["lineItems"][x]["quantity"]
                    else:
                        count_products[orders_date_result["checkoutForms"][ind]["lineItems"][x]["offer"]["name"]] += \
                            orders_date_result["checkoutForms"][ind]["lineItems"][x]["quantity"]

            n += 100
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
