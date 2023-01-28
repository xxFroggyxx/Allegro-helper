import codecs
import datetime
import json
import os
import threading
import tkinter
import webbrowser
import AllegroHelper

import customtkinter

DATA = {}
if os.path.exists("expiring.txt"):
    with open("expiring.txt") as f:
        for line in f:
            key, value = line.strip().split('>>>')
            DATA[key] = value


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
        self.authorization_label = customtkinter.CTkLabel(master=self.authorization_layout, text="Autoryzuj użytkownika", font=("Calibri", 32))
        self.authorization_label.place(relx=.5, rely=.3, anchor=tkinter.N)
        self.authorization_button = customtkinter.CTkButton(master=self.authorization_layout, text="Zaloguj", width=150, height=40,
                                                            command=threading.Thread(target=self.authorize_user).start)
        self.authorization_button.place(relx=.5, rely=.6, anchor=tkinter.N)

        # Functional layout
        self.functional_layout = customtkinter.CTkFrame(master=self, width=375, height=375, corner_radius=10)
        self.functional_label = customtkinter.CTkLabel(master=self.functional_layout, text="Wybierz co chcesz zrobić", font=("Calibri", 32))
        self.functional_label.place(relx=.5, rely=.3, anchor=tkinter.N)
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
        code = AllegroHelper.get_code()
        dev = json.loads(code.text)
        webbrowser.open(dev['verification_uri_complete'])
        self.access_token = AllegroHelper.await_for_access_token(int(dev['interval']), dev['device_code'])
        self.switch_layout()

    def download_orders_with_date_border(self):
        now = datetime.datetime.now().date()
        date_dialog = customtkinter.CTkInputDialog(text="YYYY-MM-DD", title="Podaj date")
        value_date_dialog = date_dialog.get_input()
        if value_date_dialog == "" or len(value_date_dialog) < 9:
            return

        result = AllegroHelper.get_orders_with_date_border(self.access_token, str(value_date_dialog))
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
