import time

import scraper
import requests
import pickle
import yaml
from datetime import datetime
from urllib.parse import quote as urlencode

_seen = None
_filename = 'seen.pickle'


def get_persistent():
    global _seen
    if _seen is None:
        try:
            with open(_filename, 'rb') as f:
                _seen = pickle.load(f)
        except (EOFError, FileNotFoundError):
            _seen = []
            save_persistent()
    return _seen


def save_persistent():
    global _seen
    if _seen is None:
        raise RuntimeError
    with open(_filename, 'wb+') as f:
        pickle.dump(_seen, f)


def main():
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0'}
    cfg = yaml.safe_load(open("config.yaml", "r"))
    url = cfg['url'].replace('?!!?', urlencode(cfg['search']))
    endpoint = f'https://api.telegram.org/bot{cfg["tg_token"]}/sendMessage'

    while True:
        r = requests.get(url, headers=headers)
        vacancies = scraper.parse(r.text)
        seen = get_persistent()
        new_cnt = 0
        for vacancy in vacancies:
            if vacancy[0] in seen:
                break
            new_cnt += 1
            seen.append(vacancy[0])

            message = f'<a href="{vacancy[4]}"><b>{vacancy[1]}</b> [{vacancy[2]}]</a>' \
                      + f'\n{vacancy[5] if vacancy[5] else "Зарплата не указана"}' \
                      + f'\n\n{vacancy[3]}'
            send = requests.get(endpoint,
                                params={
                                    'chat_id': cfg['chat_id'],
                                    'text': message,
                                    'parse_mode': 'HTML',
                                    'disable_web_page_preview': True,
                                })
            if send.status_code != 200:
                print(send.json())
                raise ConnectionError
        save_persistent()
        print(f'[{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}] Heartbeat: '
              f'{new_cnt} new out of {len(vacancies)} vacancies')
        time.sleep(30)


if __name__ == '__main__':
    main()
