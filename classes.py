from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from tgrpc import classes as tgrpc_classes


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
    instrument: tgrpc_classes.Instrument = None

    @staticmethod
    def from_api_data(pp: tgrpc_classes.PortfolioPosition,
                      instrument: tgrpc_classes.Instrument,
                      current_market_price: Decimal,
                      today_market_rate: Decimal, today_cb_rate: Decimal):
        """Создает объект позиции в портфолио из данных, получаемых по API

        Args:
            pp (tgrpc_classes.PortfolioPosition): позиция из API
            instrument (tgrpc_classes.Instrument): инструмент Позиции
            current_market_price (Decimal): текущая цена на рынке из API
            today_market_rate (Decimal): курс обмена валюты позиции по рынку
            today_cb_rate (Decimal): курс обмена валюты позиции по ЦБ

        Returns:
            PortfolioPosition: объект позиции портфолио со всеми данными
        """
        currency = instrument.currency.upper()

        pos = PortfolioPosition(pp.figi, instrument.name, instrument.ticker, Decimal(pp.balance), pp.instrument_type,
                                currency, pp.average_position_price.ammount,
                                exp_yield=pp.expected_yield)

        pos.current_market_price = current_market_price
        pos.today_market_rate = today_market_rate
        pos.today_cb_rate = today_cb_rate

        pos.average_position_price = pp.average_position_price
        # pos.average_position_price_no_nkd = pp.average_position_price_no_nkd
        # pos.blocked = pp.blocked
        pos.expected_yield = pp.expected_yield
        pos.isin = instrument.isin
        # pos.lots = pp.lots

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
        if self.current_market_price is None:
            return 0
        return self.current_market_price * Decimal(self.balance)

    @property
    def market_cost_rub_cb(self):
        return self.market_cost * self.today_cb_rate

    @property
    def market_value_rub(self):
        # market value RUB (total cost for figi position)
        return self.market_cost * self.today_market_rate

    @property
    def percent_change(self):
        if self.market_price is None:
            return 0
        if self.ave_price > 0:
            return ((self.market_price / self.ave_price) * 100) - 100
        return 0

    @property
    def sum_buy(self):
        return Decimal(self.ave_price) * Decimal(self.balance)

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
    op_category: str
    op_date: datetime
    op_currency: str
    op_payment: Decimal
    op_ticker: str
    op_payment_rub: Decimal
    op_figi: str
    op_status: str

    @property
    def op_in_last_12_months(self):
        return self.op_in_last_365_days

    @property
    def op_in_last_365_days(self):
        tz_info = self.op_date.tzinfo
        return self.op_date > datetime.now(tz_info) - timedelta(days=365)
