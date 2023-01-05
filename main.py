import requests
import json
import time
import os
import datetime
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
    try:
        payload = {'client_id': CLIENT_ID}
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        api_call_response = requests.post(CODE_URL, auth=(CLIENT_ID, CLIENT_SECRET),
                                          headers=headers, data=payload, verify=True)
        return api_call_response
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def get_access_token(device_code):
    try:
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        data = {'grant_type': 'urn:ietf:params:oauth:grant-type:device_code', 'device_code': device_code}
        api_call_response = requests.post(TOKEN_URL, auth=(CLIENT_ID, CLIENT_SECRET),
                                          headers=headers, data=data, verify=True)
        return api_call_response
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def await_for_access_token(interval, device_code):
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
            expire_time = now + datetime.timedelta(hours=10)
            with open("expiring.txt", "w") as f:
                f.write(f"EXPIRE_TIME>>>{expire_time.strftime('%Y-%m-%d %H:%M:%S')}\nACCESS_TOKEN>>>{token['access_token']}")

            return token['access_token']


def get_orders(token):
    try:
        url = "https://api.allegro.pl/order/checkout-forms"
        headers = {'Authorization': 'Bearer ' + token, 'Accept': "application/vnd.allegro.public.v1+json"}
        orders_result = requests.get(url, headers=headers, verify=True)
        return orders_result
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def main():
    code = get_code()
    result = json.loads(code.text)

    if len(DATA) != 0:
        now = datetime.datetime.now()
        expire_time = datetime.datetime.strptime(DATA['EXPIRE_TIME'], '%Y-%m-%d %H:%M:%S')

        if now > expire_time:
            print("User, open this address in the browser:" + result['verification_uri_complete'])
            access_token = await_for_access_token(int(result['interval']), result['device_code'])
        else:
            access_token = DATA['ACCESS_TOKEN']

    else:
        print("User, open this address in the browser:" + result['verification_uri_complete'])
        access_token = await_for_access_token(int(result['interval']), result['device_code'])

    orders = get_orders(access_token)
    print(json.dumps(orders.json(), indent=4))


if __name__ == "__main__":
    main()
