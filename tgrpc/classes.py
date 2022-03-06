from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from typing import Dict, Union

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

from tgrpc.service import (bond_price_calculation,
                           futures_price_calculation
                           )

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
    opened_date: datetime
    closed_date: datetime
    type: int
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
        currency = money_ammount.currency.upper()
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
        open_out = bond_price_calculation(open, nominal)

        close = Price.fromQuotation(candle.close).ammount
        close_out = bond_price_calculation(close, nominal)

        high = Price.fromQuotation(candle.high).ammount
        high_out = bond_price_calculation(high, nominal)

        low = Price.fromQuotation(candle.low).ammount
        low_out = bond_price_calculation(low, nominal)

        return Candle(open_out,
                      close_out,
                      high_out,
                      low_out,
                      candle.volume,
                      candle.time.ToDatetime(),
                      candle.is_complete)

    @staticmethod
    def futures_candle_from_api(candle,
                                min_price_increment=Decimal(1.0),
                                min_price_increment_amount=Decimal(1.0)):
        """Возвращает свечу для Облигации с коррекцией на номинал

        Args:
            candle (): свеча из API
            nominal (Decimal, optional): Номинал облигации. Defaults to Decimal(1000).

        Returns:
            Candle: корректированная свеча облигации
        """
        open = Price.fromQuotation(candle.open).ammount
        open_out = futures_price_calculation(open,
                                             min_price_increment,
                                             min_price_increment_amount)

        close = Price.fromQuotation(candle.close).ammount
        close_out = futures_price_calculation(close,
                                              min_price_increment,
                                              min_price_increment_amount)

        high = Price.fromQuotation(candle.high).ammount
        high_out = futures_price_calculation(high,
                                             min_price_increment,
                                             min_price_increment_amount)

        low = Price.fromQuotation(candle.low).ammount
        low_out = futures_price_calculation(low,
                                            min_price_increment,
                                            min_price_increment_amount)

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
        self.currency = money.currency.upper()
        self.ammount = Price.fromQuotation(money).ammount

    @property
    def balance(self):
        # for backward compatibility
        return self.ammount


@dataclass
class FutureMargin():
    initial_margin_on_buy: Decimal  # Гарантийное обеспечение при покупке.
    initial_margin_on_sell: Decimal  # Гарантийное обеспечение при продаже.
    min_price_increment: Decimal  # Шаг цены.
    min_price_increment_amount: Decimal  # Стоимость шага цены.
    currency: Union[str,None] = None

    @staticmethod
    def from_api(margins):
        initial_margin_on_buy = MoneyAmmount.fromMoneyAmmount(margins.initial_margin_on_buy)
        initial_margin_on_sell = MoneyAmmount.fromMoneyAmmount(margins.initial_margin_on_sell)
        min_price_increment = Decimal(margins.min_price_increment)
        min_price_increment_amount = Price.fromQuotation(margins.min_price_increment_amount)
        currency = initial_margin_on_buy.currency.upper()
        return FutureMargin(initial_margin_on_buy.ammount,
                            initial_margin_on_sell.ammount,
                            min_price_increment,
                            min_price_increment_amount.ammount,
                            currency)


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
            instrument.currency.upper(),
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
    state: int
    quantity: int
    figi: str
    instrument_type: str
    date: datetime
    type: str  # Название из API
    type_code: int  # Код из API
    quantity_rest: int = 0
    parent_operation_id: Union[str,None] = None

    @property
    def category(self):
        try:
            return OPERATION_TYPES[self.type_code]["category"]
        except Exception:
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
            operation.currency.upper(),
            MoneyAmmount.fromMoneyAmmount(operation.payment),
            MoneyAmmount.fromMoneyAmmount(operation.price),
            operation.state,
            operation.quantity,
            operation.figi,
            operation.instrument_type,
            operation.date.ToDatetime(),
            operation.type,
            operation.operation_type,
            operation.quantity_rest,
            operation.parent_operation_id
        )


OPERATION_TYPES = {
    operations_pb2.OPERATION_TYPE_UNSPECIFIED: {
        "name": "Тип операции не определён",
        "category": None
        },
    operations_pb2.OPERATION_TYPE_INPUT: {
        "name": "Завод денежных средств",
        "category": "PayIn"
        },
    operations_pb2.OPERATION_TYPE_BOND_TAX: {
        "name": "Удержание налога по купонам",
        "category": "TaxCoupon"
        },
    operations_pb2.OPERATION_TYPE_OUTPUT_SECURITIES: {
        "name": "Вывод ЦБ",
        "category": ""
        },
    operations_pb2.OPERATION_TYPE_OVERNIGHT: {
        "name": "Доход по сделке РЕПО овернайт",
        "category": ""
        },
    operations_pb2.OPERATION_TYPE_TAX: {
        "name": "Удержание налога",
        "category": "Tax"
        },
    operations_pb2.OPERATION_TYPE_BOND_REPAYMENT_FULL: {
        "name": "Полное погашение облигаций",
        "category": "Repa"
        },
    operations_pb2.OPERATION_TYPE_SELL_CARD: {
        "name": "Продажа ЦБ с карты",
        "category": "Sell"
        },
    operations_pb2.OPERATION_TYPE_DIVIDEND_TAX: {
        "name": "Удержание налога по дивидендам",
        "category": "TaxDividend"
        },
    operations_pb2.OPERATION_TYPE_OUTPUT: {
        "name": "Вывод денежных средств",
        "category": "PayOut"
        },
    operations_pb2.OPERATION_TYPE_BOND_REPAYMENT: {
        "name": "Частичное погашение облигаций",
        "category": ""
        },
    operations_pb2.OPERATION_TYPE_TAX_CORRECTION: {
        "name": "Корректировка налога",
        "category": "Tax"
        },
    operations_pb2.OPERATION_TYPE_SERVICE_FEE: {
        "name": "Удержание комиссии за обслуживание брокерского счёта",
        "category": "ServiceCommission"
        },
    operations_pb2.OPERATION_TYPE_BENEFIT_TAX: {
        "name": "Удержание налога за материальную выгоду",
        "category": "Tax"
        },
    operations_pb2.OPERATION_TYPE_MARGIN_FEE: {
        "name": "Удержание комиссии за непокрытую позицию",
        "category": "ServiceCommission"
        },
    operations_pb2.OPERATION_TYPE_BUY: {
        "name": "Покупка ЦБ",
        "category": "Buy"
        },
    operations_pb2.OPERATION_TYPE_BUY_CARD: {
        "name": "Покупка ЦБ с карты",
        "category": "Buy"
        },
    operations_pb2.OPERATION_TYPE_INPUT_SECURITIES: {
        "name": "Завод ЦБ",
        "category": "PayIn"
        },
    operations_pb2.OPERATION_TYPE_SELL_MARGIN: {
        "name": "Продажа в результате Margin-call",
        "category": "Sell"
        },
    operations_pb2.OPERATION_TYPE_BROKER_FEE: {
        "name": "Удержание комиссии за операцию",
        "category": "BrokerCommission"
        },
    operations_pb2.OPERATION_TYPE_BUY_MARGIN: {
        "name": "Покупка в результате Margin-call",
        "category": "Buy"
        },
    operations_pb2.OPERATION_TYPE_DIVIDEND: {
        "name": "Выплата дивидендов",
        "category": "Dividend"
        },
    operations_pb2.OPERATION_TYPE_SELL: {
        "name": "Продажа ЦБ",
        "category": "Sell"
        },
    operations_pb2.OPERATION_TYPE_COUPON: {
        "name": "Выплата купонов",
        "category": "Coupon"
        },
    operations_pb2.OPERATION_TYPE_SUCCESS_FEE: {
        "name": "Удержание комиссии SuccessFee",
        "category": "ServiceCommission"
        },
    operations_pb2.OPERATION_TYPE_DIVIDEND_TRANSFER: {
        "name": "Передача дивидендного дохода",
        "category": ""
        },
    operations_pb2.OPERATION_TYPE_ACCRUING_VARMARGIN: {
        "name": "Зачисление вариационной маржи",
        "category": ""
        },
    operations_pb2.OPERATION_TYPE_WRITING_OFF_VARMARGIN: {
        "name": "Списание вариационной маржи",
        "category": ""
        },
    operations_pb2.OPERATION_TYPE_DELIVERY_BUY: {
        "name": "Покупка в рамках экспирации фьючерсного контракта",
        "category": "Buy"
        },
    operations_pb2.OPERATION_TYPE_DELIVERY_SELL: {
        "name": "Продажа в рамках экспирации фьючерсного контракта",
        "category": "Sell"
        },
    operations_pb2.OPERATION_TYPE_TRACK_MFEE: {
        "name": "Комиссия за управление по счёту автоследования",
        "category": "Comission"
        },
    operations_pb2.OPERATION_TYPE_TRACK_PFEE: {
        "name": "Комиссия за результат по счёту автоследования",
        "category": "Comission"
        },
    operations_pb2.OPERATION_TYPE_TAX_PROGRESSIVE: {
        "name": "Удержание налога по ставке 15%",
        "category": "Tax"
        },
    operations_pb2.OPERATION_TYPE_BOND_TAX_PROGRESSIVE: {
        "name": "Удержание налога по купонам по ставке 15%",
        "category": "TaxCoupon"
        },
    operations_pb2.OPERATION_TYPE_DIVIDEND_TAX_PROGRESSIVE: {
        "name": "Удержание налога по дивидендам по ставке 15%",
        "category": "TaxDividend"
        },
    operations_pb2.OPERATION_TYPE_BENEFIT_TAX_PROGRESSIVE: {
        "name": "Удержание налога за материальную выгоду по ставке 15%",
        "category": "Tax"
        },
    operations_pb2.OPERATION_TYPE_TAX_CORRECTION_PROGRESSIVE: {
        "name": "Корректировка налога по ставке 15%",
        "category": "Tax"
        },
    operations_pb2.OPERATION_TYPE_TAX_REPO_PROGRESSIVE: {
        "name": "Удержание налога за возмещение по сделкам РЕПО по ставке 15%",
        "category": "Tax"
        },
    operations_pb2.OPERATION_TYPE_TAX_REPO: {
        "name": "Удержание налога за возмещение по сделкам РЕПО",
        "category": "Tax"
        },
    operations_pb2.OPERATION_TYPE_TAX_REPO_HOLD: {
        "name": "Удержание налога по сделкам РЕПО",
        "category": "Tax"
        },
    operations_pb2.OPERATION_TYPE_TAX_REPO_REFUND: {
        "name": "Возврат налога по сделкам РЕПО",
        "category": "Tax"
        },
    operations_pb2.OPERATION_TYPE_TAX_REPO_HOLD_PROGRESSIVE: {
        "name": "Удержание налога по сделкам РЕПО по ставке 15%",
        "category": "Tax"
        },
    operations_pb2.OPERATION_TYPE_TAX_REPO_REFUND_PROGRESSIVE: {
        "name": "Возврат налога по сделкам РЕПО по ставке 15%",
        "category": "Tax"
        },
    operations_pb2.OPERATION_TYPE_DIV_EXT: {
        "name": "Выплата дивидендов на карту",
        "category": "PayOut"
        },
}


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
    average_position_price_pt: Union[Decimal,None] = None  # Для фьючерсов

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
                                 Price.fromQuotation(position.quantity).ammount,
                                 MoneyAmmount.fromMoneyAmmount(position.average_position_price),
                                 MoneyAmmount.fromMoneyAmmount(position.current_nkd).ammount,
                                 Price.fromQuotation(position.expected_yield).ammount,
                                 Price.fromQuotation(position.average_position_price_pt).ammount
                                 )
