# get all necessary data from Tinkoff API
import logging
from datetime import datetime

import tinvest
from pytz import timezone


def parse_text_file(logger=logging.getLogger()):
    logger.info('getting account data..')
    token_file = open(file='my_account.txt')
    my_token = token_file.readline().rstrip('\n')
    my_timezone = timezone(token_file.readline().rstrip('\n'))
    start_year = token_file.readline().rstrip('\n')
    start_month = token_file.readline().rstrip('\n')
    start_day = token_file.readline().rstrip('\n')
    token_file.close()
    now_date = datetime.now()
    start_date = datetime(int(start_year), int(start_month), int(start_day), 0, 0, 0, tzinfo=my_timezone)
    logger.info('account started: ' + start_date.strftime('%Y %b %d '))
    return {'my_token': my_token, 'my_timezone': my_timezone, 'start_date': start_date, 'now_date': now_date}


def get_api_data(logger=logging.getLogger()):
    logger.info("authorisation..")
    client = tinvest.SyncClient(account_data['my_token'])
    logger.info("authorisation success")
    positions = client.get_portfolio()
    operations = client.get_operations(from_=account_data['start_date'], to=account_data['now_date'])
    course_usd = client.get_market_orderbook(figi='BBG0013HGFT4', depth=20)
    course_eur = client.get_market_orderbook(figi='BBG0013HJJ31', depth=20)
    currencies = client.get_portfolio_currencies()
    logger.info("portfolio received")
    market_rate_today = {'USD': course_usd.payload.last_price,
                         'EUR': course_eur.payload.last_price,
                         'RUB': 1}
    return positions, operations, market_rate_today, currencies


account_data = parse_text_file()
