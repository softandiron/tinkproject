from tinvest import Portfolio, PortfolioPosition
from tinvest.schemas import InstrumentType, MoneyAmount, Currency

from decimal import Decimal

dummy_positions = [
    PortfolioPosition(
        name='Дамми Oracle',
        averagePositionPrice=MoneyAmount(currency=Currency('USD'), value=Decimal(77.69)),
        averagePositionPriceNoNkd=None,
        balance=Decimal(25),
        blocked=None,
        expectedYield=MoneyAmount(currency=Currency('USD'), value=Decimal(280.55)),
        figi='BBG000BQLTW7',
        instrumentType=InstrumentType('Stock'),
        isin='US68389X1054',
        lots=25,
        ticker='ORCL'
    ),

    PortfolioPosition(
        name='Дамми Credit Bank of Moscow',
        averagePositionPrice=MoneyAmount(currency=Currency('USD'), value=Decimal(1050.8333)),
        averagePositionPriceNoNkd=MoneyAmount(currency=Currency('USD'), value=Decimal(1015)),
        balance=Decimal(5),
        blocked=None,
        expectedYield=MoneyAmount(currency=Currency('RUB'), value=Decimal(110.0)),
        figi='BBG00G9DSXZ5',
        instrumentType=InstrumentType('Bond'),
        isin='XS1589106910',
        lots=25,
        ticker='XS1589106910'
    ),

    PortfolioPosition(
        name='Дамми Тинькофф S&P 500',
        averagePositionPrice=MoneyAmount(currency=Currency('USD'), value=Decimal(0.1081)),
        averagePositionPriceNoNkd=MoneyAmount(currency=Currency('USD'), value=Decimal(1015)),
        balance=Decimal(999),
        blocked=None,
        expectedYield=MoneyAmount(currency=Currency('RUB'), value=Decimal(4.8)),
        figi='TCS00A102EQ8',
        instrumentType=InstrumentType('Etf'),
        isin='RU000A102EQ8',
        lots=9,
        ticker='TSPX'
    ),

    PortfolioPosition(
        name='Дамми Доллар',
        averagePositionPrice=MoneyAmount(currency=Currency('RUB'), value=Decimal(73.25)),
        averagePositionPriceNoNkd=None,
        balance=Decimal(1000000),
        blocked=None,
        expectedYield=MoneyAmount(currency=Currency('RUB'), value=Decimal(100.25)),
        figi='BBG0013HGFT4',
        instrumentType=InstrumentType('Currency'),
        isin=None,
        lots=2,
        ticker='USD000UTSTOM'
    )
]

my_portfolio = Portfolio(positions=dummy_positions)
