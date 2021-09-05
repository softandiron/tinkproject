import sqlite3
from datetime import datetime

import logging
from decimal import Decimal

db_file_name = "assets_db.db"

db_logger = logging.getLogger("DB")
db_logger.setLevel(logging.INFO)


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


try:
    db_logger.debug("Connecting to the DB...")
    sqlite_connection = sqlite3.connect(db_file_name)
    cursor = sqlite_connection.cursor()
    init_database()
except sqlite3.Error as error:
    db_logger.error("Error connecting database", error)


if __name__ == '__main__':

    close_database_connection()
