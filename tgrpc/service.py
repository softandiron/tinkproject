from decimal import Decimal
import logging


logger = logging.getLogger("tgrpc-service")


def bond_price_calculation(raw_price, nominal):
    """Расчет реальной цены облигации в валюте

    Args:
        raw_price (Decimal): цена в процентах номинала
        nominal (Decimal): номинал облигации

    Returns:
        Decimal: цена в валюте облигации
    """
    # https://tinkoff.github.io/investAPI/faq_marketdata/#_4
    logger.debug("Calculate True Bond price")
    price = Decimal(raw_price/100*nominal)
    logger.debug("Calculate True Bond price")
    return price


def futures_price_calculation(raw_price, min_price_increment, min_price_increment_amount):
    """Расчет реальной цены фьчерсов в валюте

    Args:
        raw_price (Decimal): цена в пунктах
        min_price_increment (Decimal): шаг цены
        min_price_increment_ammount (Decimal): стоимость шага цены

    Returns:
            Decimal: цена в валюте фьчерса
    """
    # https://tinkoff.github.io/investAPI/faq_marketdata/#futures
    # **price** / **min_price_increment** * **min_price_increment_amount**

    logger.debug("Calculate True Future price")
    logger.debug(f"{raw_price} / {min_price_increment} * {min_price_increment_amount}")
    price = raw_price / min_price_increment * min_price_increment_amount
    logger.debug(price)
    return Decimal(price)
