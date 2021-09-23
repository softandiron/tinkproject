from tinvest import Portfolio, PortfolioPosition
from tinvest.schemas import InstrumentType, MoneyAmount, Currency

from decimal import Decimal

dummy_positions = [
    # PortfolioPosition(
    # name='Бумажка',
    # averagePositionPrice=MoneyAmount(currency=Currency('RUB'),value='100'),
    # averagePositionPriceNoNkd=None,
    # balance=1000000,
    # blocked=None,
    # expectedYield=MoneyAmount(currency=Currency('RUB'),value='100500'),
    # figi='BBBBBBUMAZHKA',
    # instrumentType=InstrumentType('Stock'),
    # isin='BUMBUMBUM01',
    # lots=5,
    # ticker='BUMAZHKA'
    # ),

    PortfolioPosition(
    name='Доллар США',
    averagePositionPrice=MoneyAmount(currency=Currency('RUB'),value=Decimal(73.25)),
    averagePositionPriceNoNkd=None,
    balance=Decimal(1000000),
    blocked=None,
    expectedYield=MoneyAmount(currency=Currency('RUB'),value=Decimal(100.25)),
    figi='BBG0013HGFT4',
    instrumentType=InstrumentType('Currency'),
    isin=None,
    lots=2,
    ticker='USD000UTSTOM'
    )
]

my_portfolio = Portfolio(positions=dummy_positions)
