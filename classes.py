import math
import pytz
from datetime import datetime, timedelta
from dataclasses import dataclass

import logging
import data_parser
from decimal import Decimal

db_logger = logging.getLogger("DB")
db_logger.setLevel(logging.INFO)


@dataclass
class PortfolioHistoryObject:
    account_id: str
    figi: str
    buy_date: datetime
    buy_ammount: int
    buy_price: Decimal
    buy_currency: str
    buy_operation_id: str
    sell_date: datetime = None
    sell_ammount: int = None
    sell_price: Decimal = None
    sell_currency: str = None
    sell_operation_id: str = None
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

    def ticker(self):
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
        return self.sell_total_rub() - self.buy_total_rub()
