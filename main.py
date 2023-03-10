import time

import scraper
import requests
import pickle
import yaml
from datetime import datetime
from utils import time_fmt

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
    cfg = yaml.safe_load(open("config.yaml", "r"))
    hh_endpoint = 'https://api.hh.ru/vacancies'  # Contrary to docs, it doesn't require auth
    headers = {'User-Agent': cfg['user_agent']}
    data = {'text': cfg['search'], 'order_by': 'publication_time', 'per_page': cfg['per_page']}
    if area := cfg['area_id']:
        data['area_id'] = area
    if role := cfg['professional_role']:
        data['professional_role'] = role

    telegram_endpoint = f'https://api.telegram.org/bot{cfg["tg_token"]}/sendMessage'

    connection_errors = 0
    while True:
        # noinspection PyBroadException
        try:
            r = requests.get(hh_endpoint, headers=headers, data=data)
            connection_errors = 0
        except Exception:
            connection_errors += 1
            print(f'{time_fmt()} #{connection_errors} connection error(s) in a row')
            if connection_errors > 10:
                print(f'''{time_fmt()} Trying to notify user on telegram: {requests.get(telegram_endpoint,
                            params={
                                "chat_id": cfg["chat_id"],
                                "text": "Невозможно подключиться к HH, перезапусти меня!"
                            }).status_code()}''')
                raise ConnectionError
            time.sleep(cfg['sleep_delay_secs'])
            continue

        vacancies = scraper.parse(r.json())
        seen = get_persistent()
        new_vacancies = 0
        blacklisted = 0
        for vacancy in vacancies:
            if vacancy[0] in seen:
                continue
            seen.append(vacancy[0])
            if any([i.lower() in vacancy[1].lower() for i in cfg['title_blacklist_words']]):
                blacklisted += 1
                continue
            new_vacancies += 1

            message = f'<a href="{vacancy[4]}"><b>{vacancy[1]}</b> [{vacancy[2]}]</a>' \
                      + f'\n{vacancy[5] if vacancy[5] else "Зарплата не указана"}' \
                      + f'\n\n{vacancy[3]}'
            send = requests.get(telegram_endpoint,
                                params={
                                    'chat_id': cfg['chat_id'],
                                    'text': message,
                                    'parse_mode': 'HTML',
                                    'disable_web_page_preview': True,
                                })
            if send.status_code != 200:
                print(f'{time_fmt()} Error sending to telegram: {send.json()}')
                raise ConnectionError

        save_persistent()
        print(f'[{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}] Heartbeat: '
              f'{new_vacancies} new ({blacklisted} new blacklisted) out of {len(vacancies)} vacancies')
        time.sleep(cfg['sleep_delay_secs'])


if __name__ == '__main__':
    main()
