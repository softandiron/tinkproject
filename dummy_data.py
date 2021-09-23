from tinvest import Portfolio, PortfolioPosition
from tinvest.schemas import InstrumentType, MoneyAmount, Currency

from decimal import Decimal

dummy_positions = [PortfolioPosition(
    name='Доллар США',
    average_position_price=MoneyAmount(currency=Currency('RUB'),value='73.0'),
    average_position_price_no_nkd=None,
    balance=1000000,
    blocked=None,
    expected_yield=MoneyAmount(currency=Currency('RUB'),value='175.0'),
    figi='BBG0013HGFT4',
    instrument_type=InstrumentType('Currency'),
    isin=None,
    lots=2,
    ticker='USD000UTSTOM'
)
]

my_portfolio = Portfolio(positions=dummy_positions)
