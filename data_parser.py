# get all necessary data from Tinkoff API
import logging

import time
from pytz import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from decimal import Decimal

import tinvest
from pycbrf.rates import ExchangeRate
from pycbrf.toolbox import ExchangeRates

# creating ruble 1:1 exchange rate for cleaner iterating over currencies
ruble = ExchangeRate(code='RUB', value=Decimal(1), rate=Decimal(1), name='Рубль', id='KOSTYL', num='KOSTYL',
                     par=Decimal(1))
delay_time = 0.1


def get_exchange_rate(date):
    rate = ExchangeRates(date)
    rate.rates.append(ruble)
    return rate


def calc_investing_period(logger):
    start_date = account_data['start_date'].replace(tzinfo=None)
    current_date = account_data['now_date']
    inv_period = relativedelta(current_date, start_date)
    logger.info('investing period: ' + str(inv_period.years) + ' years ' + str(inv_period.months) + ' months '
                                                                         + str(inv_period.days) + ' days')
    return inv_period


def generate_date_range():
    start_date = account_data['start_date'].replace(tzinfo=None)
    current_date = account_data['now_date']
    for n in range(int((current_date - start_date).days)):
        yield datetime.date(start_date + timedelta(n))


def loop_dates(logger=logging.getLogger()):
    logger.info('parsing rates for each date from Central Bank..')
    day_rates = {}
    for each_date in generate_date_range():
        date = each_date
        rates = get_exchange_rate(date)
        usd = rates['USD'].value
        eur = rates['EUR'].value
        rub = Decimal(1)
        day_rates.update({date: {'USD': usd, 'EUR': eur, 'RUB': rub}})
        time.sleep(delay_time)
    rates = get_exchange_rate(account_data['now_date'])
    # add the today day
    day_rates.update({datetime.date(account_data['now_date'].replace(tzinfo=None)): {'USD': rates['USD'].value,
                                                                                     'EUR': rates['EUR'].value,
                                                                                     'RUB': Decimal(1)}})
    logger.info('all the rates are saved')
    return day_rates


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
