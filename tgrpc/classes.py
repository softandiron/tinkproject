from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from tgrpc.users_pb2 import (ACCOUNT_TYPE_INVEST_BOX,
                             ACCOUNT_TYPE_TINKOFF,
                             ACCOUNT_TYPE_TINKOFF_IIS,
                             ACCOUNT_TYPE_UNSPECIFIED
                             )

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
class MoneyAmmount():
    currency: str
    ammount: Decimal

    def __init__(self, money_ammount):
        self.currency = money_ammount.currency
        units = money_ammount.units
        nano = money_ammount.nano
        self.ammount = Decimal(units) + Decimal(nano)/Decimal(1000000000)


@dataclass
class PortfolioPosition():
    figi: str
    instrument_type: str
    quantity: Decimal
    average_position_price: MoneyAmmount  # Средняя цена покупки
    current_nkd: Decimal
    expected_yield: Decimal  # Накопленная ожидаемая прибыль - НКД в ней?
    average_position_price_pt: Decimal = None  # Для фьючерсов

    @property
    def balance(self):
        return self.quantity

    @staticmethod
    def from_api(position):
        return PortfolioPosition(position.figi,
                                 position.instrument_type,
                                 Decimal(position.quantity),
                                 MoneyAmmount(position.average_position_price),
                                 MoneyAmmount(position.current_nkd),
                                 Decimal(position.expected_yield),
                                 position.average_position_price_pt
                                 )
