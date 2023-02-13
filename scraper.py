import re

html_tag = re.compile('<.*?>')


def parse(body: dict) -> [(int, str, str, str, str)]:
    vacancies = []
    for vacancy in body['items']:
        vacancy_id = int(vacancy['id'])
        title = vacancy['name']
        employer = vacancy['employer']['name']
        description = '\n\n'.join([i for i in vacancy['snippet'].values() if i is not None]) \
            if vacancy['snippet'] else ''
        description = re.sub(html_tag, '', description)
        url = vacancy['alternate_url']
        if s := vacancy['salary']:
            suffix = f'{"р." if s["currency"] == "RUR" else s["currency"]} ' \
                     f'{"до вычета налогов" if s["gross"] == True else ""}'
            salary = f'{"от " + str(s["from"]) + " " if s["from"] else ""}{"до " + str(s["to"]) if s["to"] else ""}' \
                     + suffix
        else:
            salary = 'Зарплата не указана'

        vacancies.append((vacancy_id, title, employer, description, url, salary))

    return vacancies


def main():
    import requests

    r = requests.get('https://api.hh.ru/vacancies?text=java&area=1', headers={'User-Agent': 'TestBot/0.1'})
    iterated = False
    vacancies = parse(r.json())
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
