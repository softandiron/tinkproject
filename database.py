import sqlite3
from datetime import datetime

import logging
from decimal import Decimal
from tinvest.schemas import SearchMarketInstrument

db_logger = logging.getLogger("DB")
db_logger.setLevel(logging.INFO)


class Database:
    __instance = None

    def __new__(self, *args):
        # Singleton - позволяет иметь только один экземпляр класса
        if self.__instance is None:
            self.__instance = object.__new__(self, *args)
        return self.__instance

    def __init__(self, db_file_name="assets_db.db"):
        self.db_file_name = db_file_name
        self.open_database_connection(db_file_name)

    def init_database(self):
        db_logger.debug("Checking exchange rates table")
        rates_sql = """CREATE TABLE IF NOT EXISTS rates (
            date TEXT,
            currency TEXT,
            rate TEXT,
            PRIMARY KEY (date, currency)
        ) WITHOUT ROWID;
        """
        try:
            self.cursor.execute(rates_sql)
            self.sqlite_connection.commit()
        except Exception as e:
            db_logger.error(e)

        db_logger.debug("Checking instruments cache table")
        instruments_sql = """CREATE TABLE IF NOT EXISTS instruments (
            timestamp timestamp,
            figi TEXT,
            ticker TEXT,
            name TEXT,
            currency TEXT,
            type TEXT,
            lot INTEGER,
            min_price_increment TEXT,
            isin TEXT,
            PRIMARY KEY (figi)
        ) WITHOUT ROWID;
        """
        try:
            self.cursor.execute(instruments_sql)
            self.sqlite_connection.commit()
        except Exception as e:
            db_logger.error("Error creating instruments table", e)

        db_logger.debug("Checking marketprice cache table")
        marketprice_sql = """CREATE TABLE IF NOT EXISTS marketprice (
            timestamp timestamp,
            figi TEXT,
            price TEXT,
            PRIMARY KEY (figi)
        ) WITHOUT ROWID;
        """
        try:
            self.cursor.execute(marketprice_sql)
            self.sqlite_connection.commit()
        except Exception as e:
            db_logger.error("Error creating marketprice table", e)

    def close_database_connection(self):
        self.sqlite_connection.commit()
        self.cursor.close()
        self.sqlite_connection.close()

    def get_exchange_rate(self, date=datetime.now(), currency="USD"):
        date_str = date.strftime("%Y-%m-%d")
        db_logger.debug(f"Get rate for {currency} on {date_str}")
        sql_s = "SELECT * FROM rates where date = ? and currency = ?;"
        try:
            row = self.cursor.execute(sql_s, (date_str, currency)).fetchone()
        except sqlite3.Error as e:
            db_logger.error("Error getting rate", e)
        if not row:
            return None
        return Decimal(row[2])

    def put_exchange_rate(self, date=datetime.now(), currency="USD", rate=1.0):
        date_str = date.strftime("%Y-%m-%d")
        db_logger.debug(f"Put rate {rate} for {currency} on {date_str}")
        sql = "INSERT OR REPLACE INTO rates (date, currency, rate) VALUES (?, ?, ?);"
        try:
            self.cursor.execute(sql, (date_str, currency, str(rate)))
            self.sqlite_connection.commit()
        except sqlite3.Error as e:
            db_logger.error("Rate insertion error", e)
            return False
        return True

    def put_instrument(self, instrument):
        date_str = datetime.now()
        ticker = instrument.ticker
        figi = instrument.figi
        db_logger.debug(f"Put instrument {ticker} - {figi}")
        sql = """INSERT OR REPLACE INTO instruments (timestamp,
            figi, ticker, name, currency,
            type, lot, min_price_increment, isin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        try:
            self.cursor.execute(sql, (date_str,
                                      figi, ticker, instrument.name, instrument.currency,
                                      instrument.type, str(instrument.lot),
                                      str(instrument.min_price_increment), instrument.isin))
            self.sqlite_connection.commit()
        except sqlite3.Error as e:
            db_logger.error("Instrument insertion error", e)
            return False
        return True

    def get_instrument_by_figi(self, figi, max_age=7*24*60*60):
        # max_age - timeout of getting old - default - 1 week
        db_logger.debug(f"Get instrument for {figi}")
        sql_s = "SELECT * FROM instruments where figi = ?;"
        try:
            row = self.cursor.execute(sql_s, (figi,)).fetchone()
            if row and datetime.now().timestamp() - row['timestamp'].timestamp() > max_age:
                db_logger.debug(f"Instrument for {figi} is too old")
                row = None
        except sqlite3.Error as e:
            db_logger.error("Error getting instrument", e)
        if not row or row is None:
            return None
        db_logger.debug(f"Returning good instrument for {figi}")
        instrument = SearchMarketInstrument(figi=row['figi'],
                                            ticker=row['ticker'],
                                            lot=row['lot'],
                                            name=row['name'],
                                            type=row['type'],
                                            currency=row['currency'],
                                            min_price_increment=row['min_price_increment'],
                                            isin=row['isin'])
        return instrument

    def put_market_price(self, figi, price=Decimal(1.0)):
        date_str = datetime.now()
        db_logger.debug(f"Put market price for {figi}")
        sql = """INSERT OR REPLACE INTO marketprice (timestamp,
            figi, price)
            VALUES (?, ?, ?);"""
        try:
            self.cursor.execute(sql, (date_str, figi, str(price)))
            self.sqlite_connection.commit()
        except sqlite3.Error as e:
            db_logger.error("Marketprice insertion error", e)
            return False
        return True

    def get_market_price_by_figi(self, figi, max_age=10*60):
        # max_age - timeout of getting old - default - 10 minutes
        db_logger.debug(f"Get market price for {figi}")
        sql_s = "SELECT * FROM marketprice where figi = ?;"
        try:
            row = self.cursor.execute(sql_s, (figi,)).fetchone()
            if row and datetime.now().timestamp() - row['timestamp'].timestamp() > max_age:
                db_logger.debug(f"Market price for {figi} is too old")
                row = None
        except sqlite3.Error as e:
            db_logger.error("Error getting market price", e)
        if not row or row is None:
            return None
        db_logger.debug(f"Returning market price for {figi}")
        return Decimal(row['price'])

    def open_database_connection(self, db_file_name="assets_db.db"):
        try:
            db_logger.debug("Connecting to the DB...")
            self.sqlite_connection = sqlite3.connect(db_file_name,
                                                     detect_types=sqlite3.PARSE_DECLTYPES |
                                                     sqlite3.PARSE_COLNAMES)
            self.sqlite_connection.row_factory = sqlite3.Row
            self.cursor = self.sqlite_connection.cursor()
            self.init_database()
        except sqlite3.Error as error:
            db_logger.error("Error connecting database", error)


if __name__ == '__main__':
    db = Database()
    db.open_database_connection()
    db.close_database_connection()
