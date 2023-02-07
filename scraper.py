from bs4 import BeautifulSoup
from urllib.parse import urlparse


def parse(body: str) -> [(int, str, str, str, str)]:
    soup = BeautifulSoup(body, 'html.parser')
    vacancies = []
    for _vacancy in soup.select('div.serp-item'):
        vacancy = _vacancy.next
        header = vacancy.next.next
        href = header.find(class_='serp-item__title')
        vacancy_full_url = href.get('href')
        vacancy_id = int(urlparse(vacancy_full_url).path.split('/')[-1])

        vacancy_title = href.text
        vacancy_employer = header.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'}).text
        try:
            vacancy_payment = header.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'}).text
        except AttributeError:
            vacancy_payment = ''

        v_body = _vacancy.find('div', class_='g-user-content')  # .find(class_='vacancy-serp-item__info')
        try:
            vacancy_description = v_body.get_text(separator='\n')
        except AttributeError as e:
            vacancy_description = ''

        vacancies.append((vacancy_id, vacancy_title, vacancy_employer, vacancy_description, vacancy_full_url,
                          vacancy_payment))

    return vacancies


def main():
    import requests

    r = requests.get('https://hh.ru/search/vacancy?text=java&area=1',
                     headers={
                         'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0'})
    iterated = False
    vacancies = parse(r.text)
    for vacancy in vacancies:
        iterated = True
        print(f'[{vacancy[0]}] {vacancy[1]} {{{vacancy[2]}}}\n{vacancy[3]}')
        print('==========================================')

    if not iterated:
        print('[[Новых вакансий нет]]')


if __name__ == '__main__':
    import time

    while True:
        main()
        time.sleep(30)
