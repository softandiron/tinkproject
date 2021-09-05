# get all necessary data from Tinkoff API
import decimal
import logging

import time
from pytz import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from decimal import Decimal

import tinvest
from pycbrf.rates import ExchangeRate
from pycbrf.toolbox import ExchangeRates

import database
from currencies import currencies_data, supported_currencies

logger = logging.getLogger("Parser")
logger.setLevel(logging.INFO)

# creating ruble 1:1 exchange rate for cleaner iterating over currencies
ruble = ExchangeRate(code='RUB', value=Decimal(1), rate=Decimal(1), name='Рубль', id='KOSTYL', num='KOSTYL',
                     par=Decimal(1))
delay_time = 0.1


def get_exchange_rate_db(date=datetime.now(), currency="USD"):
    rate = database.get_exchange_rate(date, currency)
    if rate:
        return rate
    # Если курс не найден
    logger.info(f"Need to get rates for {date} from CB")
    rates = get_exchange_rate(date)
    for curr in supported_currencies:
        curr_rate = rates[curr].value
        database.put_exchange_rate(date, curr, curr_rate)
    return get_exchange_rate_db(date, currency)


def get_exchange_rates_for_date_db(date):
    rates = {}
    for currency in supported_currencies:
        rates[currency] = get_exchange_rate_db(date, currency)
    return rates


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


def parse_text_file():
    logger.info('getting account data..')
    with open(file='my_account.txt') as token_file:
        my_token = token_file.readline().rstrip('\n')
        my_timezone = timezone(token_file.readline().rstrip('\n'))
        start_year = token_file.readline().rstrip('\n')
        start_month = token_file.readline().rstrip('\n')
        start_day = token_file.readline().rstrip('\n')

    now_date = datetime.now()
    start_date = datetime(int(start_year), int(start_month), int(start_day), 0, 0, 0, tzinfo=my_timezone)
    logger.info('account started: ' + start_date.strftime('%Y %b %d '))
    return {'my_token': my_token, 'my_timezone': my_timezone, 'start_date': start_date, 'now_date': now_date}

def get_accounts(logger=logging.getLogger()):
    logger.info('getting accounts')
    client = tinvest.SyncClient(account_data['my_token'])
    accounts = client.get_accounts()
    logging.debug(accounts)
    logger.info('accounts received')
    return accounts

def get_api_data(broker_account_id, logger=logging.getLogger()):
    logger.info("authorisation..")
    client = tinvest.SyncClient(account_data['my_token'])
    logger.info("authorisation success")
    positions = client.get_portfolio(broker_account_id=broker_account_id)
    operations = client.get_operations(from_=account_data['start_date'], to=account_data['now_date'], broker_account_id=broker_account_id)
    market_rate_today = {}
    for currency, data in currencies_data.items():
        if 'figi' in data.keys():
            course = client.get_market_orderbook(figi=data['figi'], depth=0)
            market_rate_today[currency] = course.payload.last_price
        else:
            market_rate_today[currency] = 1
    currencies = client.get_portfolio_currencies(broker_account_id=broker_account_id)
    logger.info("portfolio received")

    return positions, operations, market_rate_today, currencies


def get_current_market_price(figi):
    client = tinvest.SyncClient(account_data['my_token'])
    book = client.get_market_orderbook(figi=figi, depth=20)
    price = book.payload.last_price
    return price


def get_position_type(figi):
    client = tinvest.SyncClient(account_data['my_token'])
    position_data = client.get_market_search_by_figi(figi)
    type = position_data.payload.type
    return type


def get_instrument_by_figi(figi):
    client = tinvest.SyncClient(account_data['my_token'])
    instrument = client.get_market_search_by_figi(figi)
    return  instrument


account_data = parse_text_file()
