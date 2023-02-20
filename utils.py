from datetime import datetime


def time_fmt():
    return f'[{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}]'
