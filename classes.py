import math
import pytz

from dataclasses import dataclass
from datetime import datetime, timedelta

import logging
import data_parser
from decimal import Decimal

from tinvest import schemas as tschemas


@dataclass
class PortfolioPosition:
    figi: str
    name: str
    ticker: str
    balance: Decimal
    position_type: str
    currency: str
    ave_price: Decimal
    exp_yield: Decimal = None

    ave_buy_price_rub: Decimal = None

    average_position_price: Decimal = None
    average_position_price_no_nkd: Decimal = None
    blocked: Decimal = None
    expected_yield: Decimal = None
    current_market_price: Decimal = None  # реальные данные с биржи
    isin: str = None
    lots: int = 0
    today_market_rate: Decimal = 1  # Курс валюты по бирже
    today_cb_rate: Decimal = 1  # Курс валюты по центробанку
    instrument: tschemas.MarketInstrument = None

    @staticmethod
    def from_api_data(pp: tschemas.PortfolioPosition,
                      instrument: tschemas.MarketInstrument,
                      current_market_price: Decimal,
                      today_market_rate: Decimal, today_cb_rate: Decimal):
        """Создает объект позиции в портфолио из данных, получаемых по API

        Args:
            pp (tschemas.PortfolioPosition): позиция из API
            instrument (tschemas.MarketInstrument): инструмент Позиции
            current_market_price (Decimal): текущая цена на рынке из API
            today_market_rate (Decimal): курс обмена валюты позиции по рынку
            today_cb_rate (Decimal): курс обмена валюты позиции по ЦБ

        Returns:
            PortfolioPosition: объект позиции портфолио со всеми данными
        """

        pos = PortfolioPosition(pp.figi, pp.name, pp.ticker, pp.balance, instrument.type,
                                pp.average_position_price.currency, pp.average_position_price.value,
                                exp_yield=pp.expected_yield.value)

        pos.current_market_price = current_market_price
        pos.today_market_rate = today_market_rate
        pos.today_cb_rate = today_cb_rate

        pos.average_position_price = pp.average_position_price
        pos.average_position_price_no_nkd = pp.average_position_price_no_nkd
        pos.blocked = pp.blocked
        pos.expected_yield = pp.expected_yield
        pos.isin = pp.isin
        pos.lots = pp.lots

        pos.instrument = instrument

        return pos

    @property
    def market_price(self):
        """Current price for 1 item

        Returns:
            Decimal: price for 1 item
        """
        if self.ave_price > 0 and self.position_type == "Bond":
            market_cost = self.market_cost
            # current market price for 1 item
            return round((market_cost / self.balance), 2)
        # else:
        return self.current_market_price

    @property
    def market_cost(self):
        """Total cost for all items

        Returns:
            Decimal: Total cost of figi in portfolio
        """
        if self.ave_price > 0 and self.position_type == "Bond":
            market_cost = round((self.exp_yield + (self.ave_price * self.balance)), 2)
            return market_cost
        # else:
        return self.current_market_price * self.balance

    @property
    def market_cost_rub_cb(self):
        return self.market_cost * self.today_cb_rate

    @property
    def market_value_rub(self):
        # market value RUB (total cost for figi position)
        return self.market_cost * self.today_market_rate

    @property
    def percent_change(self):
        return ((self.market_price / self.ave_price) * 100) - 100

    @property
    def sum_buy(self):
        return self.ave_price * self.balance

    @property
    def sum_buy_rub(self):
        return self.ave_buy_price_rub * self.balance

    @property
    def tax_base(self):
        if self.ave_price > 0:
            return self.market_cost_rub_cb - self.sum_buy_rub
        # in the case, if this position has ZERO purchase price
        return 0

    @property
    def exp_tax(self):
        tax_rate = 13
        return self.tax_base * Decimal(tax_rate / 100)


@dataclass
class PortfolioOperation:
    op_type: str
    op_date: datetime
    op_currency: str
    op_payment: Decimal
    op_ticker: str
    op_payment_rub: Decimal
    op_figi: str

    @property
    def op_in_last_12_months(self):
        return self.op_in_last_365_days

    @property
    def op_in_last_365_days(self):
        tz_info = self.op_date.tzinfo
        return self.op_date > datetime.now(tz_info) - timedelta(days=365)


@dataclass
class PortfolioHistoryObject:
    account_id: str
    figi: str
    buy_date: datetime
    buy_ammount: int
    buy_price: Decimal
    buy_currency: str
    buy_operation_id: str
    buy_commission: Decimal
    sell_date: datetime = None
    sell_ammount: int = None
    sell_price: Decimal = None
    sell_currency: str = None
    sell_operation_id: str = None
    sell_commission: Decimal = None
    rowid: int = None

    def days(self) -> int:
        calc_date = datetime.now(pytz.timezone("Europe/Moscow"))
        if self.sell_date is not None:
            # Если установлена дата продажи - показывает сколько активном владели
            calc_date = self.sell_date
        logging.debug(f"{calc_date} - {self.buy_date}")
        delta = calc_date - self.buy_date
        logging.debug(f"{delta} - {delta.days}")
        return delta.days

    def ticker(self) -> str:
        return data_parser.get_instrument_by_figi(self.figi).ticker

    def years_f(self) -> Decimal:
        # Возвращает количество годов с дробью, с примерной поправкой на високосные годы
        # TODO: доделать сравнение по датам в году - тогда будет точнее - а надо?
        days = self.days()
        return Decimal(round(days / 365.2425, 2))

    def years(self) -> int:
        # Возвращает полное количество годов, отбрасывая дробную часть
        # Для налогов важно полное количество лет владения
        return math.floor(self.years_f())

    def buy_total(self) -> Decimal:
        return self.buy_ammount * self.buy_price

    def buy_total_rub(self) -> Decimal:
        rate = data_parser.get_exchange_rate_db(self.buy_date, self.buy_currency)
        return self.buy_total() * rate

    def sell_total(self) -> Decimal:
        if self.sell_date is not None:
            return self.sell_ammount * self.sell_price

        price = data_parser.get_current_market_price(self.figi)
        return self.buy_ammount * price

    def sell_total_rub(self) -> Decimal:
        if self.sell_date is not None:
            rate = data_parser.get_exchange_rate_db(self.sell_date, self.sell_currency)
            return self.sell_total() * rate
        rate = data_parser.get_exchange_rate_db(currency=self.buy_currency)
        return self.sell_total() * rate

    def tax_base(self) -> Decimal:
        if self.years_f() >= 3:
            return 0
        # а как на счет отрицательной цены - это же тоже вычет!
        # налоговая база = разница цен покупки и продажи, минус комиссия покупки и продажи
        buy_rate = data_parser.get_exchange_rate_db(self.buy_date, self.buy_currency)
        buy_commission_rub = self.buy_commission * buy_rate

        sell_commission_rub = 0
        if self.sell_date is not None:
            sell_rate = data_parser.get_exchange_rate_db(self.sell_date, self.sell_currency)
            sell_commission_rub = self.sell_commission * sell_rate

        price_diff = self.sell_total_rub() - self.buy_total_rub()
        return price_diff - buy_commission_rub - sell_commission_rub
