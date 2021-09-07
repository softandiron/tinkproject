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

import csv

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
    day_rates = {}

    logger.info('downloading CB rates from saved Database..')
    with open('rates_by_date.csv', 'r') as file:
        reader = csv.reader(file)
        # creating a dictionary from csv:
        for row in reader:
            if row[0] == "date":
                continue
            date = datetime.strptime(row[0], '%Y-%m-%d').date()
            usd = decimal.Decimal(row[1])
            eur = decimal.Decimal(row[2])
            rub = decimal.Decimal(row[3])
            day_rates.update({date: {'USD': usd, 'EUR': eur, 'RUB': rub}})

        # checking for new dates, and adding them from CB API to dictionary:
        logger.info('checking for the new dates..')
        for date in generate_date_range():
            if date not in day_rates.keys():
                logger.info('new date: ' + str(date))
                rates = get_exchange_rate(date)
                usd = rates['USD'].value
                eur = rates['EUR'].value
                rub = Decimal(1)
                day_rates.update({date: {'USD': usd, 'EUR': eur, 'RUB': rub}})
                time.sleep(delay_time)

        # updating the csv file for the future:
        logger.info('updating Database..')
        with open('rates_by_date.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            for date in day_rates.keys():
                writer.writerow([date, day_rates[date]['USD'], day_rates[date]['EUR'], day_rates[date]['RUB']])

        rates = get_exchange_rate(account_data['now_date'])
        # add the today day
        day_rates.update({datetime.date(account_data['now_date'].replace(tzinfo=None)): {'USD': rates['USD'].value,
                                                                                         'EUR': rates['EUR'].value,
                                                                                         'RUB': Decimal(1)}})

    logger.info('all the rates are saved')
    return day_rates


def parse_text_file(logger=logging.getLogger()):
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
    course_usd = client.get_market_orderbook(figi='BBG0013HGFT4', depth=20)  # check this!!!
    course_eur = client.get_market_orderbook(figi='BBG0013HJJ31', depth=20)
    currencies = client.get_portfolio_currencies(broker_account_id=broker_account_id)
    logger.info("portfolio received")
    market_rate_today = {'USD': course_usd.payload.last_price,
                         'EUR': course_eur.payload.last_price,
                         'RUB': 1}

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
