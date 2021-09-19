import math
import pytz
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass

import logging
from decimal import Decimal
from tinvest.schemas import SearchMarketInstrument

db_logger = logging.getLogger("DB")
db_logger.setLevel(logging.INFO)


@dataclass
class PortfolioHistoryObject:
    account_id: str
    figi: str
    buy_date: datetime
    buy_ammount: int
    buy_price: Decimal
    buy_currency: str
    buy_operation_id: str
    sell_date: datetime = None
    sell_ammount: int = None
    sell_price: Decimal = None
    sell_currency: str = None
    sell_operation_id: str = None
    rowid: int = None

    def days(self) -> int:
        calc_date = datetime.now(pytz.timezone("Europe/Moscow"))
        if self.sell_date is not None:
            # Если установлена дата продажи - показывает сколько активном владели
            calc_date = self.sell_date
        delta = calc_date - self.buy_date
        return delta.days

    def years_f(self) -> Decimal:
        # Возвращает количество годов с дробью, с примерной поправкой на високосные годы
        # TODO: доделать сравнение по датам в году - тогда будет точнее - а надо?
        days = self.days()
        return Decimal(round(days / 365.2425, 2))

    def years(self) -> int:
        # Возвращает полное количество годов, отбрасывая дробную часть
        # Для налогов важно полное количество лет владения
        return math.floor(self.years_f())


def init_database():
    db_logger.debug("Checking exchange rates table")
    rates_sql = """CREATE TABLE IF NOT EXISTS rates (
        date TEXT,
        currency TEXT,
        rate TEXT,
        PRIMARY KEY (date, currency)
    ) WITHOUT ROWID;
    """
    try:
        cursor.execute(rates_sql)
        sqlite_connection.commit()
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
        cursor.execute(instruments_sql)
        sqlite_connection.commit()
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
        cursor.execute(marketprice_sql)
        sqlite_connection.commit()
    except Exception as e:
        db_logger.error("Error creating marketprice table", e)

    db_logger.debug("Checking portfolio history table")
    port_history_sql = """CREATE TABLE IF NOT EXISTS port_history (
        account_id TEXT,
        figi TEXT,
        buy_date TEXT,
        buy_ammount INTEGER,
        buy_price TEXT,
        buy_currency TEXT,
        buy_operation_id TEXT,
        sell_date TEXT,
        sell_ammount INTEGER,
        sell_price TEXT,
        sell_currency TEXT,
        sell_operation_id TEXT
    );"""
    port_history_idx_sql = """CREATE INDEX IF NOT EXISTS idx_port_history
    ON port_history (account_id, figi);"""
    port_history_idx_sql_buy_id = """CREATE INDEX IF NOT EXISTS idx_port_history_buy_id
    ON port_history (buy_operation_id);
    """
    port_history_idx_sql_sell_id = """CREATE INDEX IF NOT EXISTS idx_port_history_sell_id
    ON port_history (sell_operation_id);
    """
    try:
        cursor.execute(port_history_sql)
        cursor.execute(port_history_idx_sql)
        cursor.execute(port_history_idx_sql_buy_id)
        cursor.execute(port_history_idx_sql_sell_id)
        sqlite_connection.commit()
    except Exception as e:
        db_logger.error("Error creating portfolio history table", e)


def close_database_connection():
    sqlite_connection.commit()
    cursor.close()
    sqlite_connection.close()


def get_exchange_rate(date=datetime.now(), currency="USD"):
    date_str = date.strftime("%Y-%m-%d")
    db_logger.debug(f"Get rate for {currency} on {date_str}")
    sql_s = "SELECT * FROM rates where date = ? and currency = ?;"
    try:
        row = cursor.execute(sql_s, (date_str, currency)).fetchone()
    except sqlite3.Error as e:
        db_logger.error("Error getting rate", e)
    if not row:
        return None
    return Decimal(row[2])


def put_exchange_rate(date=datetime.now(), currency="USD", rate=1.0):
    date_str = date.strftime("%Y-%m-%d")
    db_logger.debug(f"Put rate {rate} for {currency} on {date_str}")
    sql = "INSERT OR REPLACE INTO rates (date, currency, rate) VALUES (?, ?, ?);"
    try:
        cursor.execute(sql, (date_str, currency, str(rate)))
        sqlite_connection.commit()
    except sqlite3.Error as e:
        db_logger.error("Rate insertion error", e)
        return False
    return True


def put_instrument(instrument):
    date_str = datetime.now()
    ticker = instrument.ticker
    figi = instrument.figi
    db_logger.debug(f"Put instrument {ticker} - {figi}")
    sql = """INSERT OR REPLACE INTO instruments (timestamp,
        figi, ticker, name, currency,
        type, lot, min_price_increment, isin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"""
    try:
        cursor.execute(sql, (date_str,
                             figi, ticker, instrument.name, instrument.currency,
                             instrument.type, str(instrument.lot),
                             str(instrument.min_price_increment), instrument.isin))
        sqlite_connection.commit()
    except sqlite3.Error as e:
        db_logger.error("Instrument insertion error", e)
        return False
    return True


def get_instrument_by_figi(figi, max_age=7*24*60*60):
    # max_age - timeout of getting old - default - 1 week
    db_logger.debug(f"Get instrument for {figi}")
    sql_s = "SELECT * FROM instruments where figi = ?;"
    try:
        row = cursor.execute(sql_s, (figi,)).fetchone()
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


def put_market_price(figi, price=Decimal(1.0)):
    date_str = datetime.now()
    db_logger.debug(f"Put market price for {figi}")
    sql = """INSERT OR REPLACE INTO marketprice (timestamp,
        figi, price)
        VALUES (?, ?, ?);"""
    try:
        cursor.execute(sql, (date_str, figi, str(price)))
        sqlite_connection.commit()
    except sqlite3.Error as e:
        db_logger.error("Marketprice insertion error", e)
        return False
    return True


def get_market_price_by_figi(figi, max_age=10*60):
    # max_age - timeout of getting old - default - 10 minutes
    db_logger.debug(f"Get market price for {figi}")
    sql_s = "SELECT * FROM marketprice where figi = ?;"
    try:
        row = cursor.execute(sql_s, (figi,)).fetchone()
        if row and datetime.now().timestamp() - row['timestamp'].timestamp() > max_age:
            db_logger.debug(f"Market price for {figi} is too old")
            row = None
    except sqlite3.Error as e:
        db_logger.error("Error getting market price", e)
    if not row or row is None:
        return None
    db_logger.debug(f"Returning market price for {figi}")
    return Decimal(row['price'])


def get_portfolio_history_records(account_id, figi="%"):
    db_logger.info(f"Get portfolio history for {figi} on account {account_id}")
    sql_s = ("SELECT rowid, * FROM port_history where account_id=? and figi LIKE ?"
             " ORDER BY  buy_date, sell_date;")
    try:
        rows = cursor.execute(sql_s, (account_id, figi)).fetchall()
    except sqlite3.Error as e:
        db_logger.error("Error getting portfolio history", e)
    out = []
    for row in rows:
        obj = PortfolioHistoryObject(row['account_id'], row['figi'],
                                     datetime.fromisoformat(row['buy_date']), 
                                     int(row['buy_ammount']), Decimal(row['buy_price']),
                                     row['buy_currency'], row['buy_operation_id'],
                                     rowid=row['rowid'])
        if row['sell_date'] is not None:
            obj.sell_date = datetime.fromisoformat(row['sell_date'])
            obj.sell_ammount = row['sell_ammount']
            obj.sell_price = Decimal(row['sell_price'])
            obj.sell_currency = row['sell_currency']
            obj.sell_operation_id = row['sell_operation_id']
        out.append(obj)
    return out


def put_portfolio_history_record(hist_object: PortfolioHistoryObject):
    db_logger.debug(f"Put portfolio history record for {hist_object.figi} "
                    "on {hist_object.account_id}")
    sql = """INSERT OR REPLACE INTO port_history (rowid, account_id,
        figi, buy_date, buy_ammount, buy_price, buy_currency, buy_operation_id,
        sell_date, sell_ammount, sell_price, sell_currency, sell_operation_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
    try:
        cursor.execute(sql, (hist_object.rowid, hist_object.account_id, hist_object.figi,
                             hist_object.buy_date, hist_object.buy_ammount,
                             str(hist_object.buy_price), hist_object.buy_currency,
                             hist_object.buy_operation_id,
                             hist_object.sell_date, hist_object.sell_ammount,
                             str(hist_object.sell_price), hist_object.sell_currency,
                             hist_object.sell_operation_id)
                       )
        sqlite_connection.commit()
    except sqlite3.Error as e:
        db_logger.critical("Portfolio insertion error", e)
        return False
    return True


def check_portfolio_history_for_id(operation_id):
    db_logger.info(f"Check portfolio history for operation {operation_id}")
    sql_s = "SELECT rowid FROM port_history where buy_operation_id=? or sell_operation_id=?;"
    row = cursor.execute(sql_s, (operation_id, operation_id)).fetchone()
    logging.debug(row)
    if row:
        return True
    return False


def open_database_connection(db_file_name="assets_db.db"):
    global sqlite_connection
    global cursor
    try:
        db_logger.debug("Connecting to the DB...")
        sqlite_connection = sqlite3.connect(db_file_name,
                                            detect_types=sqlite3.PARSE_DECLTYPES |
                                            sqlite3.PARSE_COLNAMES)
        sqlite_connection.row_factory = sqlite3.Row
        cursor = sqlite_connection.cursor()
        init_database()
    except sqlite3.Error as error:
        db_logger.error("Error connecting database", error)


if __name__ == '__main__':
    logging_level = logging.DEBUG
    logging.basicConfig(level=logging_level,
                        format='%(asctime)s [%(levelname)-3s] %(name)s: %(message)s',
                        datefmt='%H:%M:%S')
    db_logger.setLevel(logging_level)

    open_database_connection()

    test_acc = 121313
    test_figi = "TEST_FIGI"
    history = get_portfolio_history_records(test_acc, test_figi)
    print(history[2])
    print(history[2].days())
    print(history[2].years_f())
    print(history[2].years())
    print(history[0])
    print(history[0].days())
    print(history[0].years_f())
    print(history[0].years())
    # put_portfolio_history_record(test_acc, test_figi, datetime(2021, 1, 1), 3, Decimal(12.0), "MAX", rowid=1,
    #                             sell_date=datetime.now(), sell_ammount=12, sell_price=23, sell_currency="USD")
    close_database_connection()
