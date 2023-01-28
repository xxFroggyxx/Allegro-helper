import codecs
import datetime
import json
import os
import threading
import time
import tkinter
import webbrowser
from collections import OrderedDict

import customtkinter
import requests
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CODE_URL = "https://allegro.pl/auth/oauth/device"
TOKEN_URL = "https://allegro.pl/auth/oauth/token"
DATA = {}

if os.path.exists("expiring.txt"):
    with open("expiring.txt") as f:
        for line in f:
            key, value = line.strip().split('>>>')
            DATA[key] = value


def get_code():
    """Returns necessary device_code"""
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
    Helping method for await_for_access_token

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
    Returns or saves essential access_token to communicate with API and do responses with user recognition.

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
    Returns the last 100 orders which payment is done, and are ready to ship/shipped.

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
    given_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    print(f"Wszystkie przedmioty sprzedane do {given_date.date()} włącznie:")
    n = 0
    count_products = {}
    while True:
        try:
            url = f"https://api.allegro.pl/order/checkout-forms?status=READY_FOR_PROCESSING&fulfillment.status=SENT&fulfillment.status=READY_FOR_SHIPMENT&offset={n}"
            headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
            orders_date_result = requests.get(url, headers=headers, verify=True).json()

            for ind in range(len(orders_date_result["checkoutForms"])):
                product_bought_date = datetime.datetime.strptime(orders_date_result["checkoutForms"][ind]["lineItems"][0]["boughtAt"][0:10], "%Y-%m-%d")

                if given_date > product_bought_date:
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


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.access_token = None
        # Settings
        customtkinter.set_default_color_theme("green")
        self.title("Allegro helper")
        self.minsize(450, 450)
        self.geometry("500x500")

        # Authorization layout
        self.authorization_layout = customtkinter.CTkFrame(master=self, width=375, height=375, corner_radius=10)
        self.label1 = customtkinter.CTkLabel(master=self.authorization_layout, text="Autoryzuj użytkownika", font=("Calibri", 32))
        self.label1.place(relx=.5, rely=.3, anchor=tkinter.N)
        self.authorizationButton = customtkinter.CTkButton(master=self.authorization_layout, text="Zaloguj", width=150, height=40,
                                                           command=threading.Thread(target=self.authorize_user).start)
        self.authorizationButton.place(relx=.5, rely=.6, anchor=tkinter.N)

        # Functional layout
        self.functional_layout = customtkinter.CTkFrame(master=self, width=375, height=375, corner_radius=10)
        self.label2 = customtkinter.CTkLabel(master=self.functional_layout, text="Wybierz co chcesz zrobić", font=("Calibri", 32))
        self.label2.place(relx=.5, rely=.3, anchor=tkinter.N)
        self.optionButton = customtkinter.CTkButton(master=self.functional_layout, text="1. Pobierz liste produktów", height=32,
                                                    command=threading.Thread(target=self.download_orders_with_date_border).start)
        self.optionButton.place(relx=.5, rely=.6, anchor=tkinter.N)

        if len(DATA) != 0:
            self.current_layout = self.functional_layout
            self.functional_layout.pack(expand=True)

            now = datetime.datetime.now()
            expire_time = datetime.datetime.strptime(DATA['EXPIRE_TIME'], '%Y-%m-%d %H:%M:%S')
            if now > expire_time:
                self.switch_layout()
            else:
                self.access_token = DATA['ACCESS_TOKEN']

        else:
            self.current_layout = self.authorization_layout
            self.authorization_layout.pack(expand=True)

    def switch_layout(self):
        if self.current_layout == self.authorization_layout:
            self.authorization_layout.pack_forget()
            self.functional_layout.pack(expand=True)
            self.current_layout = self.functional_layout
        else:
            self.functional_layout.pack_forget()
            self.authorization_layout.pack(expand=True)
            self.current_layout = self.authorization_layout

    def authorize_user(self):
        code = get_code()
        dev = json.loads(code.text)
        webbrowser.open(dev['verification_uri_complete'])
        self.access_token = await_for_access_token(int(dev['interval']), dev['device_code'])
        self.switch_layout()

    def download_orders_with_date_border(self):
        now = datetime.datetime.now().date()
        date_dialog = customtkinter.CTkInputDialog(text="YYYY-MM-DD", title="Podaj date")
        value_date_dialog = date_dialog.get_input()
        if value_date_dialog == "" or len(value_date_dialog) < 9:
            return

        result = get_orders_with_date_border(self.access_token, str(value_date_dialog))
        suma = 0
        with codecs.open(f"{value_date_dialog} {now}.txt", "w", 'utf-8') as f:
            f.write(f"Wszystkie przedmioty sprzedane do {value_date_dialog} włącznie:\n")
            for key, value in result.items():
                f.write(f"{key} x{value}\n")
                suma += value
            f.write(f"\nSuma sprzedanych przedmiotow {suma}\n")
            f.write(f"Ilosc unikalnych przedmiotow {len(result.items())}")
        print("Zapisano")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
