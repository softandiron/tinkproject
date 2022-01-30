# get all necessary data from Tinkoff API
import decimal
import logging

import time
from pytz import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from decimal import Decimal

from configuration import Config

import tgrpc
from tgrpc.classes import CANDLE_INTERVALS
from pycbrf.rates import ExchangeRate
from pycbrf.toolbox import ExchangeRates

from database import Database
from currencies import currencies_data, supported_currencies

logger = logging.getLogger("Parser")
logger.setLevel(logging.INFO)

# creating ruble 1:1 exchange rate for cleaner iterating over currencies
ruble = ExchangeRate(code='RUB', value=Decimal(1), rate=Decimal(1), name='Рубль',
                     id='KOSTYL', num='KOSTYL', par=Decimal(1))
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


def calc_investing_period(account_id):
    start_date = config.get_account_opened_date(account_id)
    current_date = config.now_date
    inv_period = relativedelta(current_date, start_date)
    logger.info('investing period: ' + str(inv_period.years) + ' years ' + str(inv_period.months) + ' months '
                                                                         + str(inv_period.days) + ' days')
    return inv_period


def get_accounts():
    logger.info('getting accounts')
    accounts = tinkoff_access.get_accounts_list()
    logging.debug(accounts)
    logger.info('accounts received')
    # проверяем/создаем разделы для счетов в конфигурации
    # если завели новый счет - добавит с дефолтным конфигом,
    # если новые настройки были добавлены в коде - так же добавит
    config.check_accounts_config(accounts)
    return accounts


def get_api_data(broker_account_id):
    positions = tinkoff_access.get_portfolio(broker_account_id)
    operations = tinkoff_access.get_operations(broker_account_id,
                                               config.get_account_opened_date(broker_account_id),
                                               config.now_date)
    market_rate_today = {}
    for currency, data in currencies_data.items():
        if 'figi' in data.keys():
            market_rate_today[currency] = get_current_market_price(figi=data['figi'])
        else:
            market_rate_today[currency] = 1
    currencies = tinkoff_access.get_currencies(broker_account_id)
    logger.info("portfolio received")

    return positions, operations, market_rate_today, currencies


def get_current_market_price(figi, max_age=10*60):
    price = database.get_market_price_by_figi(figi, max_age)
    if price:
        return price
    instrument = get_instrument_by_figi(figi)
    try:
        price = tinkoff_access.get_last_price(figi, instrument.instrument_type)
    except Exception as e:
        logger.error("Get current market price error.")
        logger.error(e)
        return None
    database.put_market_price(figi, price)
    return price


def get_figi_history_price(figi, date=datetime.now()):
    # возвращает историческую цену актива
    # опеределяется запросом свечи за день и усреднением верхней и нижней цены
    date = datetime(date.year, date.month, date.day)
    if date == datetime.now().date():
        return get_current_market_price(figi)
    price = database.get_exchange_rate(date, figi)
    if price:
        # Если цена есть в локальной базе - не надо запрашивать API
        return price
    try:
        date_to = date + timedelta(days=1)
        candles = tinkoff_access.get_candles(figi, date, date_to, CANDLE_INTERVALS.DAY)
        price = (candles[0].h+candles[0].l)/2
    except IndexError:
        instrument = get_instrument_by_figi(figi)
        logger.error("Что-то не то со свечами! В этот день было IPO? Или размещение средств?")
        logger.error("Внебиржевая бумага?")
        logger.error(f"{date} - {figi} - {instrument.ticker}")
        logger.error(candles)
        return None
    except Exception as e:
        instrument = get_instrument_by_figi(figi)
        logger.error("Что-то не то со свечами! В этот день было IPO? Или размещение средств?")
        logger.error(f"{date} - {figi} - {instrument.ticker}")
        logger.error(candles)
        return None
    database.put_exchange_rate(date, figi, price)
    return price


def get_position_type(figi, max_age=7*24*60*60):
    # max_age - timeout for getting old, default - 1 week
    instrument = get_instrument_by_figi(figi, max_age)
    type = instrument.type
    return type


def get_instrument_by_figi(figi, instrument_type=None, max_age=7*24*60*60):
    # max_age - timeout for getting old, default - 1 week
    instrument = database.get_instrument_by_figi(figi, max_age)
    if instrument and instrument.type is not None:
        # проверка на None - чтобы избежать повтора issue #59 при старых данных в кэше
        logger.debug(f"Instrument for {figi} found in DB")
        return instrument
    logger.debug(f"Need to query instrument for {figi} from API")
    try:
        position_data = tinkoff_access.get_instrument(figi, instrument_type=instrument_type)
    except Exception as e:
        logger.error("Get instrument by figi error")
        logger.error(e)
        return None
    if instrument_type is None:
        # если был запрос на базовые данные по бумаге - дополнить тип из полученных данных
        instrument_type = position_data.instrument_type
    database.put_instrument(position_data, instrument_type)
    # print(position_data)
    return position_data


def get_ticker_by_figi(figi, instrument_type=None, max_age=7*24*60*60):
    # max_age - timeout for getting old, default - 1 week
    instrument = get_instrument_by_figi(figi, instrument_type, max_age)
    ticker = instrument.ticker
    return ticker


config = Config()
database = Database()

tinkoff_access = tgrpc.tgrpc_parser(config.token)
