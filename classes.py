import math
import pytz
from datetime import datetime, timedelta
from dataclasses import dataclass

import logging
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
        logging.error(f"{calc_date} - {self.buy_date}")
        delta = calc_date - self.buy_date
        logging.error(f"{delta} - {delta.days}")
        return delta.days

    def years_f(self) -> Decimal:
        # Возвращает количество годов с дробью, с примерной поправкой на високосные годы
        # TODO: доделать сравнение по датам в году - тогда будет точнее - а надо?
        days = self.days()
        return Decimal(round(days / 365.2425, 2))

    def years(self) -> int:
        # Возвращает полное количество годов, отбрасывая дробную часть
        # Для налогов важно полное количество лет владения
        return math.floor(self.years_f())