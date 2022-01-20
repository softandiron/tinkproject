from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import enum
import logging

from tgrpc.users_pb2 import (ACCOUNT_TYPE_INVEST_BOX,
                             ACCOUNT_TYPE_TINKOFF,
                             ACCOUNT_TYPE_TINKOFF_IIS,
                             ACCOUNT_TYPE_UNSPECIFIED
                             )
import tgrpc.instruments_pb2 as instruments_pb2
import tgrpc.marketdata_pb2 as marketdata_pb2
import tgrpc.operations_pb2 as operations_pb2

logger = logging.getLogger("tgrpc-classes")

ACCOUNT_TYPES = {
    ACCOUNT_TYPE_TINKOFF: "Tinkoff",
    ACCOUNT_TYPE_TINKOFF_IIS: "TinkoffIis",
    ACCOUNT_TYPE_INVEST_BOX: "TinkoffInvestBox",
    ACCOUNT_TYPE_UNSPECIFIED: "TinkoffUnspecified"
}

ACCOUNT_TYPES_RUS = {
    ACCOUNT_TYPE_TINKOFF: "Тинькофф",
    ACCOUNT_TYPE_TINKOFF_IIS: "ТинькоффИИС",
    ACCOUNT_TYPE_INVEST_BOX: "ТинькоффИнвесткопилка",
    ACCOUNT_TYPE_UNSPECIFIED: "ТинькоффПрочее"
}


class CANDLE_INTERVALS(enum.Enum):
    NA = marketdata_pb2.CANDLE_INTERVAL_UNSPECIFIED
    MIN_1 = marketdata_pb2.CANDLE_INTERVAL_1_MIN
    MIN_5 = marketdata_pb2.CANDLE_INTERVAL_5_MIN
    MIN_15 = marketdata_pb2.CANDLE_INTERVAL_15_MIN
    HOUR = marketdata_pb2.CANDLE_INTERVAL_HOUR
    DAY = marketdata_pb2.CANDLE_INTERVAL_DAY


class INSTRUMENT_TYPE(enum.Enum):
    Bond = 1
    Etf = 2
    Share = 3
    Currency = 4
    Future = 5


INSTRUMENT_TYPES = ["Share", "Bond", "Etf", "Currency", "Future"]


class INSTRUMENT_ID_TYPE(enum.Enum):
    Figi = instruments_pb2.INSTRUMENT_ID_TYPE_FIGI
    Ticker = instruments_pb2.INSTRUMENT_ID_TYPE_TICKER
    Isin = instruments_pb2.INSTRUMENT_ID_UNSPECIFIED


@dataclass
class Account:
    id: str
    name: str
    opened_date: str
    closed_date: str
    type: str
    status: str

    @property
    def broker_account_id(self):
        # Выдает id счета. Для обратной совместимости с кодом
        return self.id

    @property
    def broker_account_type(self):
        # Выдает тип счета. Для обратной совместимости с кодом
        return ACCOUNT_TYPES[self.type]

    @property
    def type_rus(self):
        return ACCOUNT_TYPES_RUS[self.type]


@dataclass
class Price():
    ammount: Decimal

    @staticmethod
    def fromQuotation(quotation):
        units = quotation.units
        nano = quotation.nano
        ammount = Decimal(units) + Decimal(nano)/Decimal(1000000000)
        return Price(ammount)


@dataclass
class MoneyAmmount():
    currency: str
    ammount: Decimal

    @staticmethod
    def fromMoneyAmmount(money_ammount):
        currency = money_ammount.currency
        ammount = Price.fromQuotation(money_ammount).ammount
        return MoneyAmmount(currency, ammount)


@dataclass
class Candle():
    open: Decimal
    close: Decimal
    high: Decimal
    low: Decimal
    volume: int
    time: datetime
    is_complete: bool

    @staticmethod
    def from_api(candle):
        return Candle(Price.fromQuotation(candle.open).ammount,
                      Price.fromQuotation(candle.close).ammount,
                      Price.fromQuotation(candle.high).ammount,
                      Price.fromQuotation(candle.low).ammount,
                      candle.volume,
                      candle.time.ToDatetime(),
                      candle.is_complete)

    @staticmethod
    def bond_candle_from_api(candle, nominal=Decimal(1000)):
        """Возвращает свечу для Облигации с коррекцией на номинал

        Args:
            candle (): свеча из API
            nominal (Decimal, optional): Номинал облигации. Defaults to Decimal(1000).

        Returns:
            Candle: корректированная свеча облигации
        """
        open = Price.fromQuotation(candle.open).ammount
        open_out = Decimal(open / 100 * nominal)
        close = Price.fromQuotation(candle.close).ammount
        close_out = Decimal(close / 100 * nominal)
        high = Price.fromQuotation(candle.high).ammount
        high_out = Decimal(high / 100 * nominal)
        low = Price.fromQuotation(candle.low).ammount
        low_out = Decimal(low / 100 * nominal)
        return Candle(open_out,
                      close_out,
                      high_out,
                      low_out,
                      candle.volume,
                      candle.time.ToDatetime(),
                      candle.is_complete)

    @property
    def l(self):
        # for backward compatibility
        return self.low

    @property
    def h(self):
        # for backward compatibility
        return self.high

    @property
    def o(self):
        # for backward compatibility
        return self.open

    @property
    def c(self):
        # for backward compatibility
        return self.close


@dataclass
class Currency():
    currency: str
    ammount: Decimal

    def __init__(self, money):
        self.currency = money.currency
        self.ammount = Price.fromQuotation(money).ammount

    @property
    def balance(self):
        # for backward compatibility
        return self.ammount


@dataclass
class Instrument():
    figi: str
    ticker: str
    lot: int
    name: str
    type: str   # InstrumentType
    currency: str
    min_price_increment: Decimal
    isin: str

    @staticmethod
    def from_api(instrument, instrument_type):
        isin = ""
        if instrument_type != "futures":
            isin = instrument.isin
        return Instrument(
            instrument.figi,
            instrument.ticker,
            instrument.lot,
            instrument.name,
            instrument_type,
            instrument.currency,
            instrument.min_price_increment,
            isin
        )

    @property
    def instrument_type(self):
        return self.type

@dataclass
class Operation():
    id: str
    currency: str
    payment: MoneyAmmount
    price: MoneyAmmount
    state: str
    quantity: int
    figi: str
    instrument_type: str
    date: datetime
    type: str
    quantity_rest: int = 0
    parent_operation_id: str = None

    @property
    def operation_type(self):
        # For backward compatibility
        try:
            return OPERATION_TYPES[self.type]
        except:
            logger.warning(f"Unknown operation type: {self.type}")
            return "Unknown"

    @property
    def quantity_executed(self):
        # For backward compatibility
        return self.quantity

    @property
    def status(self):
        return OPERATION_STATES[self.state]

    @staticmethod
    def from_api(operation):
        return Operation(
            operation.id,
            operation.currency,
            MoneyAmmount.fromMoneyAmmount(operation.payment),
            MoneyAmmount.fromMoneyAmmount(operation.price),
            operation.state,
            operation.quantity,
            operation.figi,
            operation.instrument_type,
            operation.date.ToDatetime(),
            operation.type,
            operation.quantity_rest,
            operation.parent_operation_id
        )


OPERATION_TYPES = {
    'Покупка ЦБ': "Buy",
    'Продажа ЦБ': "Sell",

    'Завод денежных средств': "PayIn",
    'Вывод денежных средств': "PayOut",

    'Удержание налога по дивидендам': "TaxDividend",
    'Удержание комиссии за операцию': "BrokerCommission",  # Check!!!

    'Выплата купонов': "Coupon",
    'Выплата дивидендов': "Dividend",
    'Частичное погашение облигаций': "",
    'Полное погашение облигаций': "",
    'Удержание налога': "Tax"
}


class OPERATION_TYPE(enum.Enum):
    """    'Покупка ЦБ'
        'Продажа ЦБ'

    'Завод денежных средств'

    'Удержание налога по дивидендам'
    'Удержание комиссии за операцию'

    'Выплата купонов'
    'Выплата дивидендов'
    'Частичное погашение облигаций'
    'Полное погашение облигаций'
    """

OPERATION_STATES = {
    operations_pb2.OPERATION_STATE_UNSPECIFIED: "NA",
    operations_pb2.OPERATION_STATE_EXECUTED: "Done",
    operations_pb2.OPERATION_STATE_CANCELED: "Canceled"
}


@dataclass
class PortfolioPosition():
    figi: str
    instrument_type: str
    quantity: Decimal
    average_position_price: MoneyAmmount  # Средняя цена покупки
    current_nkd: Decimal
    expected_yield: Decimal  # Накопленная ожидаемая прибыль - НКД в ней?
    average_position_price_pt: Decimal = None  # Для фьючерсов

    # name: str
    # average_position_price: Optional[MoneyAmount] = Field(alias='averagePositionPrice')
    # average_position_price_no_nkd: Optional[MoneyAmount] = Field(
    #    alias='averagePositionPriceNoNkd'
    # )
    # balance: Decimal
    # blocked: Optional[Decimal]
    # expected_yield: Optional[MoneyAmount] = Field(alias='expectedYield')
    # figi: str
    # instrument_type: InstrumentType = Field(alias='instrumentType')
    # isin: Optional[str]
    # lots: int
    # ticker: Optional[str]

    @property
    def balance(self):
        return self.quantity

    @staticmethod
    def from_api(position):
        return PortfolioPosition(position.figi,
                                 position.instrument_type,
                                 Decimal(position.quantity),
                                 MoneyAmmount.fromMoneyAmmount(position.average_position_price),
                                 MoneyAmmount.fromMoneyAmmount(position.current_nkd),
                                 Decimal(position.expected_yield),
                                 position.average_position_price_pt
                                 )
