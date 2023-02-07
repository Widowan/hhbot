import time

import scraper
import requests
import pickle
import yaml
from urllib.parse import quote as urlencode

_seen = None
_conn = None


def _get_conn():
    global _conn
    _conn = _conn if _conn is not None else open('seen.pickle', 'wb+')
    return _conn


def get_persistent():
    global _seen
    if _seen is None:
        try:
            _seen = pickle.load(_get_conn())
        except EOFError:
            _seen = []
            save_persistent()
    return _seen


def save_persistent():
    global _seen
    if _seen is None:
        raise RuntimeError
    pickle.dump(_seen, _get_conn())


def main():
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0'}
    cfg = yaml.safe_load(open("config.yaml", "r"))
    url = cfg['url'].replace('?!!?', urlencode(cfg['search']))
    endpoint = f'https://api.telegram.org/bot{cfg["tg_token"]}/sendMessage'

    while True:
        r = requests.get(url, headers=headers)
        vacancies = scraper.parse(r.text)
        for vacancy in vacancies:
            seen = get_persistent()
            if vacancy[0] in seen:
                break
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
        time.sleep(30)


if __name__ == '__main__':
    main()
