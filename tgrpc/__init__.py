import logging
from datetime import datetime, timezone
from decimal import Decimal
import time

import grpc

import tgrpc.instruments_pb2 as instruments_pb2
import tgrpc.instruments_pb2_grpc as instruments_pb2_grpc
import tgrpc.marketdata_pb2 as marketdata_pb2
import tgrpc.marketdata_pb2_grpc as marketdata_pb2_grpc
import tgrpc.operations_pb2 as operations_pb2
import tgrpc.operations_pb2_grpc as operations_pb2_grpc
import tgrpc.users_pb2 as users_pb2
import tgrpc.users_pb2_grpc as users_pb2_grpc

from tgrpc.classes import (Account,
                           Candle,
                           CANDLE_INTERVALS,
                           Currency,
                           Instrument,
                           INSTRUMENT_ID_TYPE,
                           MoneyAmmount,
                           Operation,
                           PortfolioPosition,
                           Price,
                           )

from google.protobuf.timestamp_pb2 import Timestamp

logger = logging.getLogger("tgrpc")

RATE_LIMIT_TIMEOUT = 5  # seconds


class tgrpc_parser():

    token = ""
    api_endpoint = "invest-public-api.tinkoff.ru:443"

    channel = None

    def __init__(self, token):
        self.token = token

    def get_channel(self):
        if self.channel is None:
            credentials = grpc.ssl_channel_credentials()
            composite = grpc.composite_channel_credentials(
                credentials,
                grpc.access_token_call_credentials(self.token)
                )

            self.channel = grpc.secure_channel(self.api_endpoint, composite)
        return self.channel

    def _catch_grpc_error(func):
        # Decorator function to catch GRPC errors
        def wrapper(self, *args, **kwargs):
            while True:
                try:
                    return func(self, *args, **kwargs)
                except grpc.RpcError as rpc_error:
                    error_code = rpc_error.code().__str__()
                    if error_code == "StatusCode.RESOURCE_EXHAUSTED":
                        logger.warning(f"Rate limit in {func.__name__} -> Timeout {RATE_LIMIT_TIMEOUT}s")
                        time.sleep(RATE_LIMIT_TIMEOUT)
                    elif error_code == "StatusCode.UNAUTHENTICATED":
                        logger.error("Authentication failure!")
                        logger.critical("Token incorrect!")
                        return None
                    else:
                        logger.error("Got GRPC error")
                        logger.error(rpc_error)
                        logger.error(error_code)
                        return
                except Exception as e:
                    logger.error(e)
                    return None
        return wrapper

    @_catch_grpc_error
    def get_accounts_list(self):
        stub = users_pb2_grpc.UsersServiceStub(self.get_channel())
        accounts_stub = stub.GetAccounts(users_pb2.GetAccountsRequest())
        accounts_list = []
        for account in accounts_stub.accounts:
            accounts_list.append(Account(account.id, account.name, account.opened_date,
                                         account.closed_date, account.type, account.status))
        return accounts_list

    @_catch_grpc_error
    def get_candles(self, figi, start_date, end_date, interval=CANDLE_INTERVALS.DAY):
        stub = marketdata_pb2_grpc.MarketDataServiceStub(self.get_channel())

        start_ts = Timestamp()
        start_ts.FromDatetime(start_date)
        end_ts = Timestamp()
        end_ts.FromDatetime(end_date)

        params = {"figi": figi,
                  "from": start_ts,
                  "to": end_ts,
                  "interval": interval.value
                  }
        request = marketdata_pb2.GetCandlesRequest(**params)

        candles_stub = stub.GetCandles(request)

        logger.debug(candles_stub)
        candles_out = []
        for candle in candles_stub.candles:
            candles_out.append(Candle.from_api(candle))
        return candles_out

    def get_currencies(self, account_id):
        money = self.get_positions(account_id).money
        currencies = []
        for currency in money:
            currencies.append(Currency(currency))
        return currencies

    @_catch_grpc_error
    def get_instrument_raw(self, id,
                           id_type=INSTRUMENT_ID_TYPE.Figi,
                           instrument_type=None,
                           class_code=None):
        """Запрос инструмента по Тикеру/IsIn/Figi
        Возвращает "сырые" данные из API

        Args:
            id (str): строка запроса
            id_type (INSTRUMENT_ID_TYPE): тип строки поиска - Тикеру/IsIn/Figi
            instrument_type (str): тип инструмента, или None - запросить базовую информацию
            class_code ([type]): - 	Идентификатор class_code. Обязателен при id_type = ticker.

        Запрос с типом инструмента выдает расширенную информацию. В том числе даты размещения,
        сектора, графики дивидендных и купонных выплат и т.д..
        """
        stub = instruments_pb2_grpc.InstrumentsServiceStub(self.get_channel())
        request = instruments_pb2.InstrumentRequest(id=id, id_type=id_type.value)

        if instrument_type is None:
            logger.debug(f"Get base data on instrument {id}")
            result = stub.GetInstrumentBy(request)
        elif instrument_type.lower() == "share":
            logger.debug(f"Get Share {id}")
            result = stub.ShareBy(request)
        elif instrument_type.lower() == "bond":
            logger.debug(f"Get Bond {id}")
            result = stub.BondBy(request)
        elif instrument_type.lower() == "etf":
            logger.debug(f"Get Etf {id}")
            result = stub.EtfBy(request)
        elif instrument_type.lower() == "currency":
            logger.debug(f"Get Currency {id}")
            result = stub.CurrencyBy(request)
        elif instrument_type.lower() == "future":
            logger.debug(f"Get Future {id}")
            result = stub.FutureBy(request)

        return result.instrument

    def get_instrument(self, id,
                       id_type=INSTRUMENT_ID_TYPE.Figi,
                       instrument_type=None,
                       class_code=None):
        """Запрос инструмента по Тикеру/IsIn/Figi

        Args:
            id (str): строка запроса
            id_type (str): тип строки поиска - Тикеру/IsIn/Figi
            instrument_type (): тип инструмента, или None - для запроса базовой информации
            class_code ([type]): - 	Идентификатор class_code. Обязателен при id_type = ticker.
        """
        instrument = self.get_instrument_raw(id, id_type, instrument_type, class_code)
        if instrument_type is None:
            instrument_type = instrument.instrument_type
        instrument_out = Instrument.from_api(instrument, instrument_type)
        logger.debug(instrument)
        logger.debug(instrument_out)
        logger.debug(f"Got instrument {instrument.name} - {instrument.figi}")
        return instrument_out

    @_catch_grpc_error
    def get_last_price_raw(self, figi):
        """Возвращает текущую 'сырую' цену на ОДИН Figi
        Не корректирует на номинал облигации и фьючерса,
        для облигации возвращает процент от номинала,
        для фьючерсов - индекс от номинала
        TODO: сделать возможность запроса массивом.
        Args:
            figi (str): запрашиваемый Figi

        Returns:
            Decimal: цена на запрашиваемый Figi
        """
        stub = marketdata_pb2_grpc.MarketDataServiceStub(self.get_channel())
        figis = [figi, ]

        price_stub = stub.GetLastPrices(marketdata_pb2.GetLastPricesRequest(figi=figis))

        tmp_price = price_stub.last_prices[0].price
        price = Price.fromQuotation(tmp_price).ammount
        return price

    def get_last_price(self, figi, instrument_type=None):
        """Возвращает истинную текущую цену на ОДИН Figi
        с коррекцией на номинал Облигаций и Фьючерсов
        TODO: сделать возможность запроса массивом.
        Args:
            figi (str): запрашиваемый Figi

        Returns:
            Decimal: цена на запрашиваемый Figi
        """
        raw_price = self.get_last_price_raw(figi)
        if instrument_type is None:
            instrument = self.get_instrument_raw(figi, id_type=INSTRUMENT_ID_TYPE.Figi)
            instrument_type = instrument.instrument_type
        if instrument_type.lower() == "bond":
            # сырая цена облигации - это процент от номинала
            # расчет ведется через высчитывание этой доли
            logger.info("Calculate True Bond price")
            full_instrument = self.get_instrument_raw(figi,
                                                      id_type=INSTRUMENT_ID_TYPE.Figi,
                                                      instrument_type=instrument_type)
            nominal = MoneyAmmount(full_instrument.nominal)
            price = Decimal(raw_price/100*nominal.ammount)
            return price
        elif instrument_type.lower() == "future":
            # TODO: реализовать расчет цены фьючерсов
            pass
        return raw_price

    @_catch_grpc_error
    def get_operations(self, account_id,
                       start_date=datetime(2020, 11, 1, 0, 0),
                       end_date=datetime.now(tz=timezone.utc), state="", figi=None):
        stub = operations_pb2_grpc.OperationsServiceStub(self.get_channel())

        start_ts = Timestamp()
        start_ts.FromDatetime(start_date)
        end_ts = Timestamp()
        end_ts.FromDatetime(end_date)

        params = {"account_id": account_id,
                  "from": start_ts,
                  "to": end_ts,
        #          "state": state
                  }
        if figi is not None:
            params['figi'] = figi
        request = operations_pb2.OperationsRequest(**params)
        operations_stub = stub.GetOperations(request)

        operations_out = []
        for operation in operations_stub.operations:
            operations_out.append(Operation.from_api(operation))
        return operations_out

    @_catch_grpc_error
    def get_positions(self, account_id):
        stub = operations_pb2_grpc.OperationsServiceStub(self.get_channel())
        positions_stub = stub.GetPositions(operations_pb2.PositionsRequest(account_id=account_id))
        return positions_stub

    @_catch_grpc_error
    def get_portfolio(self, account_id):
        stub = operations_pb2_grpc.OperationsServiceStub(self.get_channel())
        portfolio_stub = stub.GetPortfolio(operations_pb2.PortfolioRequest(account_id=account_id))
        # print(portfolio_stub.positions)
        portfolio_out = []
        for position in portfolio_stub.positions:
            portfolio_out.append(
                PortfolioPosition.from_api(position)
            )
        return portfolio_out