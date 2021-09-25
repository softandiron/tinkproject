from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PortfolioPosition:
    figi: str
    name: str
    ticker: str
    balance: Decimal
    position_type: str
    currency: Decimal
    ave_price: Decimal
    sum_buy: Decimal
    exp_yield: Decimal
    market_price: Decimal
    percent_change: Decimal
    market_cost: Decimal
    market_value_rub: Decimal
    market_cost_rub_cb: Decimal
    ave_buy_price_rub: Decimal
    sum_buy_rub: Decimal
    tax_base: Decimal
    exp_tax: Decimal


@dataclass
class PortfolioOperation:
    op_type: str
    op_date: str
    op_currency: str
    op_payment: Decimal
    op_ticker: str
    op_payment_rub: Decimal
    op_figi: str
    op_in_last_12_months: bool
