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
        'figi': 'BBG0013HQ5K4',
    },
    'HKD': {
        'name': 'Гонконгский доллар',
        'num_format': '# ##0,00 [$HKD]',
        'figi': 'TCS0013HSW87',
    },
    'TRY': {
        'name': 'Турецкая лира',
        'num_format': '# ##0,00 [$TRY]',
        'figi': 'BBG0013J12N1',
    },
}

supported_currencies = currencies_data.keys()
