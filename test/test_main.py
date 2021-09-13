import unittest
import main
import logging

from main import PortfolioOperation
from datetime import datetime, timezone, timedelta
from decimal import Decimal


class TestIISDeductCalculation(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # создать несколько объектов операций
        main.my_operations = [
            # покупка за 2021 год - не должно посчитать
            PortfolioOperation(op_type='Buy',
                               op_date=datetime(2021, 7, 16, 10, 40, 47, 818000, tzinfo=timezone(timedelta(seconds=10800))),
                               op_currency='RUB', op_payment=Decimal('0'), op_ticker='SBMX',
                               op_payment_rub=Decimal('-1794'), op_figi='BBG00M0C8YM7',
                               op_in_last_12_months=True),
            # пополнение за 2021 год
            PortfolioOperation(op_type='PayIn', op_date=datetime(2021, 1, 12, 10, 48, 29, tzinfo=timezone(timedelta(seconds=10800))),
                               op_currency='RUB', op_payment=Decimal('10000.0'), op_ticker='None',
                               op_payment_rub=Decimal('10000.0'), op_figi=None, op_in_last_12_months=True),
            # пополнение за 2021 год
            PortfolioOperation(op_type='PayIn', op_date=datetime(2021, 1, 12, 10, 48, 29, tzinfo=timezone(timedelta(seconds=10800))),
                               op_currency='RUB', op_payment=Decimal('10000.0'), op_ticker='None',
                               op_payment_rub=Decimal('10000.0'), op_figi=None, op_in_last_12_months=True),
            # пополнение за 2019 год с превышением максимальной суммы пополнения
            PortfolioOperation(op_type='PayIn', op_date=datetime(2019, 1, 12, 10, 48, 29, tzinfo=timezone(timedelta(seconds=10800))),
                               op_currency='RUB', op_payment=Decimal('2000000.0'), op_ticker='None',
                               op_payment_rub=Decimal('2000000.0'), op_figi=None, op_in_last_12_months=True),
            # пополнение за 2020 год в долларах
            PortfolioOperation(op_type='PayIn', op_date=datetime(2020, 1, 12, 10, 48, 29, tzinfo=timezone(timedelta(seconds=10800))),
                               op_currency='USD', op_payment=Decimal('2000000.0'), op_ticker='None',
                               op_payment_rub=Decimal('2000000.0'), op_figi=None, op_in_last_12_months=True),
        ]
        # итого должно быть 20000*0,13 = 2600 за 2021 год
        # 2020 год - ничего - так как пополнение было в долларах
        # 2019 год - база 4000000, вычет 52000, предупреждение о превышении пополнения

    def test_deduct_non_IIS_account(self):
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)
        main.logger = logging.getLogger("calculator")
        main.sum_profile = {}
        main.sum_profile['broker_account_type'] = "Tinkoff"
        main.logger.setLevel(logging.DEBUG)
        with self.assertLogs(logger=main.logger, level=logging.DEBUG) as logs:
            self.assertIsNone(main.calculate_iis_deduction())
        self.assertEqual(logs.records[0].getMessage(), "account is not of IIS Type")

    def test_deduct_IIS_account(self):
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)
        main.logger = logging.getLogger("calculator")
        main.sum_profile = {}
        main.sum_profile['broker_account_type'] = "TinkoffIis"
        self.assertIsNotNone(main.calculate_iis_deduction())

        test_etalon = {2021: {'pay_in': Decimal('20000.00'), 'base': Decimal('20000.0'),
                              'deduct': Decimal('2600.00')},
                       2019: {'pay_in': Decimal('2000000.00'), 'base': Decimal('400000'),
                              'deduct': Decimal('52000.00')},
                       0: Decimal('54600.00')}

        with self.assertLogs(logger=main.logger) as logs:
            self.assertDictEqual(test_etalon, main.calculate_iis_deduction())
        messages = []
        for record in logs.records:
            messages.append(record.getMessage())
        # проверка на превышение размера взносов за год
        self.assertIn("Взносы на ИИС в 2019г. больше лимита на взносы 1000000р "
                      "и составили 2000000.0р",
                      messages)
        # проверка на превышение суммы налоговой базы за год
        self.assertIn("Взносы на ИИС в 2019г. больше лимита на вычет 400000р, "
                      "составили 2000000.0р. Налоговая база скорректирована.",
                      messages)
        # проверка на пополнение не в рублях
        self.assertIn("Пополнение ИИС в 2020 году не в рублях!",
                      messages)
