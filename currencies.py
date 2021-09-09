"""Хранилище данных о валютах
"""

currencies_data = {
    'RUB': {
        'name': 'Российский рубль',
        'num_format': '## ### ##0.00   [$₽-ru-RU]',
    },
    'USD': {
        'name': 'Доллар США',
        'num_format': '## ### ##0.00   [$$-409]',
        'figi': 'BBG0013HGFT4',
    },
    'EUR': {
        'name': 'Евро',
        'num_format': '## ### ##0.00   [$€-x-euro1]',
        'figi': 'BBG0013HJJ31',
    },
    'CHF': {
        'name': 'Швейцарский франк',
        'num_format': '## ### ##0.00   [$CHF-fr-CH]',
        # TODO: find figi for CHFRUB
    },
}

supported_currencies = currencies_data.keys()
