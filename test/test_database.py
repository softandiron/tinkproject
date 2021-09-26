from decimal import Decimal
import unittest
from database import Database
import time
import os

from datetime import datetime
from tinvest.schemas import SearchMarketInstrument


class TestDatabaseFunctionality(unittest.TestCase):
    db_file_name = "assets_test_db.db"

    @classmethod
    def setUpClass(self):
        self.database = Database(self.db_file_name)

    @classmethod
    def tearDownClass(self):
        self.database.close_database_connection()
        os.remove(self.db_file_name)

    test_figi = "TSTFIGIT"
    test_figi2 = "TSTFIGIT2"
    instrument = SearchMarketInstrument(figi=test_figi,
                                        ticker="TSTT",
                                        lot=1,
                                        name="Test variant Stock",
                                        type="Stock",
                                        currency="RUB",
                                        min_price_increment=Decimal(0.5),
                                        isin="tst20210907")
    instrument2 = SearchMarketInstrument(figi=test_figi2,
                                         ticker="TST2",
                                         lot=10,
                                         name="Test variant Stock",
                                         type="Stock",
                                         currency="RUB")

    def test_rates_table_insert(self):
        self.assertTrue(self.database.put_exchange_rate())
        self.assertTrue(self.database.put_exchange_rate(currency="RUB"))
        self.assertTrue(self.database.put_exchange_rate(rate=2.0))
        self.assertTrue(self.database.put_exchange_rate(date=datetime(2016, 6, 1)))
        self.assertTrue(self.database.put_exchange_rate(date=datetime(2016, 5, 1),
                                                        currency="RUB", rate="2.5"))

    def test_rates_table_get_correct_rate(self):
        # Курс должен быть получен
        test_date = datetime(2016, 5, 1)
        self.database.put_exchange_rate(date=test_date,
                                        currency="RUB", rate="2.5")
        self.database.put_exchange_rate(rate=Decimal(2.256))
        self.assertEqual(self.database.get_exchange_rate(), Decimal(2.256))
        self.assertIsNotNone(self.database.get_exchange_rate(date=test_date, currency="RUB"))
        self.assertEqual(self.database.get_exchange_rate(date=test_date, currency="RUB"), 2.5)

    def test_rates_table_get_no_rate(self):
        # Курс не должен быть получен
        test_date = datetime(2016, 5, 1)
        test_date2 = datetime(2021, 1, 1)
        self.database.put_exchange_rate(date=test_date,
                                        currency="RUB", rate="2.5")
        self.database.put_exchange_rate(rate=Decimal(2.256))
        self.assertIsNone(self.database.get_exchange_rate(date=test_date2, currency="TST"))
        self.assertIsNone(self.database.get_exchange_rate(date=test_date, currency="TST"))
        self.assertIsNone(self.database.get_exchange_rate(currency="TST"))

    def test_instrument_put(self):
        with self.assertRaises(TypeError):
            self.database.put_instrument()
        self.assertTrue(self.database.put_instrument(self.instrument))
        self.assertTrue(self.database.put_instrument(self.instrument2))
        self.assertFalse(None)
        pass

    def test_instrument_get_correct(self):
        self.database.put_instrument(self.instrument)
        self.database.put_instrument(self.instrument2)
        self.assertEqual(self.database.get_instrument_by_figi(self.test_figi), self.instrument)
        self.assertEqual(self.database.get_instrument_by_figi(self.test_figi2), self.instrument2)
        self.assertNotEqual(self.database.get_instrument_by_figi(self.test_figi), self.instrument2)
        self.assertNotEqual(self.database.get_instrument_by_figi(self.test_figi2), self.instrument)
        non_existent_figi = "TSTN"
        self.assertNotEqual(self.database.get_instrument_by_figi(non_existent_figi),
                            self.instrument)
        self.assertNotEqual(self.database.get_instrument_by_figi(non_existent_figi),
                            self.instrument2)
        self.assertIsNone(self.database.get_instrument_by_figi(non_existent_figi))
        pass

    def test_instrument_expire(self):
        self.database.put_instrument(self.instrument)
        self.database.put_instrument(self.instrument2)
        time.sleep(1)
        # еще не устарело - по умолчанию - неделя
        self.assertEqual(self.database.get_instrument_by_figi(self.test_figi),
                         self.instrument)
        # еще не устарело - отложено на 1 секунду, задаем 10
        self.assertEqual(self.database.get_instrument_by_figi(self.test_figi, max_age=10),
                         self.instrument)
        # точно устарело - прошло более 1 секунды
        self.assertNotEqual(self.database.get_instrument_by_figi(self.test_figi, max_age=1),
                            self.instrument)
        # устарело и вывело None
        self.assertIsNone(self.database.get_instrument_by_figi(self.test_figi, max_age=1))

    def test_market_price_put(self):
        with self.assertRaises(TypeError):
            self.database.put_market_price()
        self.assertTrue(self.database.put_market_price(self.test_figi))
        self.assertTrue(self.database.put_market_price(self.test_figi2, Decimal(4.555)))
        self.assertTrue(self.database.put_market_price(self.test_figi), Decimal(2.5))  # overwrite

    def test_market_price_get_correct(self):
        self.database.put_market_price(self.test_figi)
        self.assertEqual(self.database.get_market_price_by_figi(self.test_figi), Decimal(1.0))

        self.database.put_market_price(self.test_figi, Decimal(2.5))  # overwrite
        self.assertNotEqual(self.database.get_market_price_by_figi(self.test_figi), Decimal(1.0))
        self.assertEqual(self.database.get_market_price_by_figi(self.test_figi), Decimal(2.5))

        self.database.put_market_price(self.test_figi2, Decimal(4.555))
        self.assertEqual(self.database.get_market_price_by_figi(self.test_figi2), Decimal(4.555))
        self.assertNotEqual(self.database.get_market_price_by_figi(self.test_figi2), Decimal(2.5))
        self.assertNotEqual(self.database.get_market_price_by_figi(self.test_figi), Decimal(4.555))

        non_existent_figi = "NONEXFIG"
        self.assertIsNone(self.database.get_market_price_by_figi(non_existent_figi))

    def test_market_price_expire(self):
        self.database.put_market_price(self.test_figi, Decimal(2.5))
        self.database.put_market_price(self.test_figi2, Decimal(4.555))
        time.sleep(1)

        # еще не устарело - по умолчанию - неделя
        self.assertEqual(self.database.get_market_price_by_figi(self.test_figi), Decimal(2.5))
        # еще не устарело - отложено на 1 секунду, задаем 10
        self.assertEqual(self.database.get_market_price_by_figi(self.test_figi, max_age=10),
                         Decimal(2.5))
        # точно устарело - прошло более 1 секунды
        self.assertNotEqual(self.database.get_instrument_by_figi(self.test_figi, max_age=1),
                            Decimal(2.5))
        # устарело и вывело None
        self.assertIsNone(self.database.get_instrument_by_figi(self.test_figi, max_age=1))
        pass


if __name__ == '__main__':
    unittest.main()
