# get all necessary data from Tinkoff API

import tinvest
from datetime import datetime
from pytz import timezone


def parse_text_file():
    print('getting account data..')
    token_file = open(file='my_account.txt')
    my_token = token_file.readline().rstrip('\n')
    my_timezone = timezone(token_file.readline().rstrip('\n'))
    start_year = token_file.readline().rstrip('\n')
    start_month = token_file.readline().rstrip('\n')
    start_day = token_file.readline().rstrip('\n')
    token_file.close()
    now_date = datetime.now()
    start_date = datetime(int(start_year), int(start_month), int(start_day), 0, 0, 0, tzinfo=my_timezone)

    acc_data = {'my_token': my_token, 'my_timezone': my_timezone, 'start_date': start_date, 'now_date': now_date}
    print('account started: ' + start_date.strftime('%Y %b %d '))

    return acc_data


account_data = parse_text_file()


def get_api_data():
    print("authorisation..")
    client = tinvest.SyncClient(account_data['my_token'])
    print("- authorisation success")

    positions = client.get_portfolio()
    operations = client.get_operations(from_=account_data['start_date'], to=account_data['now_date'])
    course_usd = client.get_market_orderbook(figi='BBG0013HGFT4', depth=20)
    course_eur = client.get_market_orderbook(figi='BBG0013HJJ31', depth=20)
    currencies = client.get_portfolio_currencies()

    return positions, operations, course_usd.payload.last_price, course_eur.payload.last_price, currencies
