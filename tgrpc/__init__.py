import logging
from datetime import datetime, timezone
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
                           CANDLE_INTERVALS,
                           INSTRUMENT_ID_TYPE,
                           Operation,
                           PortfolioPosition,
                           )

from decimal import Decimal  # TODO: убрать из зависимостей в классы
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

    def get_accounts_list(self):
        stub = users_pb2_grpc.UsersServiceStub(self.get_channel())
        accounts_stub = stub.GetAccounts(users_pb2.GetAccountsRequest())
        accounts_list = []
        for account in accounts_stub.accounts:
            accounts_list.append(Account(account.id, account.name, account.opened_date,
                                         account.closed_date, account.type, account.status))
        return accounts_list

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
        try:
            candles_stub = stub.GetCandles(request)
        except grpc.RpcError as rpc_error:
            error_code = rpc_error.code().__str__()
            if error_code == "StatusCode.RESOURCE_EXHAUSTED":
                logger.warning(f"Rate limit in get_candles -> Timeout {RATE_LIMIT_TIMEOUT}s")
                time.sleep(RATE_LIMIT_TIMEOUT)
                return self.get_last_price(figi)
            logger.error("Get candles error")
            logger.error(rpc_error)
            logger.error(error_code)
        logger.info(candles_stub)
        return None

    def get_instrument_by(self, id,
                          id_type=INSTRUMENT_ID_TYPE.Figi,
                          instrument_type="Share",
                          class_code=None):
        """Запрос инструмента по Тикеру/IsIn/Figi

        Args:
            id (str): строка запроса
            id_type (str): тип строки поиска - Тикеру/IsIn/Figi 
            instrument_type (): тип инструмента
            class_code ([type]): - 	Идентификатор class_code. Обязателен при id_type = ticker.
        """
        stub = instruments_pb2_grpc.InstrumentsServiceStub(self.get_channel())
        request = instruments_pb2.InstrumentRequest(id=id, id_type=id_type.value)
        try:
            if instrument_type.lower() in ["share", "stock"]:  # TODO: stock - убрать после - оставлено для обратной совместимости.
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
        except grpc.RpcError as rpc_error:
            error_code = rpc_error.code().__str__()
            if error_code == "StatusCode.RESOURCE_EXHAUSTED":
                logger.warning(f"Rate limit in get_instrument -> Timeout {RATE_LIMIT_TIMEOUT}s")
                time.sleep(RATE_LIMIT_TIMEOUT)
                return self.get_instrument_by(id, id_type, instrument_type, class_code)
            logger.error("Get instrument error")
            logger.error(rpc_error)
            logger.error(error_code)
        except Exception as e:
            logger.error(e)
            logger.error(id, id_type, instrument_type, class_code)
            return None

        logger.debug(result.instrument)
        logger.debug(f"Got instrument {result.instrument.name} - {result.instrument.figi}")
        return result.instrument

    def get_last_price(self, figi):
        """Возвращает текущую цену на ОДИН Figi
        TODO: сделать возможность запроса массивом.
        Args:
            figi (str): запрашиваемый Figi

        Returns:
            Decimal: цена на запрашиваемый Figi
        """
        stub = marketdata_pb2_grpc.MarketDataServiceStub(self.get_channel())
        figis = [figi, ]
        try:
            price_stub = stub.GetLastPrices(marketdata_pb2.GetLastPricesRequest(figi=figis))
        except grpc.RpcError as rpc_error:
            error_code = rpc_error.code().__str__()
            if error_code == "StatusCode.RESOURCE_EXHAUSTED":
                logger.warning(f"Rate limit in get_last_price -> Timeout {RATE_LIMIT_TIMEOUT}s")
                time.sleep(RATE_LIMIT_TIMEOUT)
                return self.get_last_price(figi)
            logger.error("Get last price error")
            logger.error(rpc_error)
            logger.error(error_code)
        tmp_price = price_stub.last_prices[0].price
        price = Decimal(tmp_price.units) + Decimal(tmp_price.nano)/Decimal(1000000000)
        return price

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
        try:
            operations_stub = stub.GetOperations(request)
        except grpc.RpcError as rpc_error:
            error_code = rpc_error.code().__str__()
            if error_code == "StatusCode.RESOURCE_EXHAUSTED":
                logger.warning(f"Rate limit in get_operations -> Timeout {RATE_LIMIT_TIMEOUT}s")
                time.sleep(RATE_LIMIT_TIMEOUT)
                return self.get_operations(account_id, start_date, end_date, figi)
            logger.error("Get operation error")
            logger.error(rpc_error)
            logger.error(error_code)
        operations_out = []
        for operation in operations_stub.operations:
            operations_out.append(Operation.from_api(operation))
        return operations_out

    def get_positions(self, account_id):
        stub = operations_pb2_grpc.OperationsServiceStub(self.get_channel())
        positions_stub = stub.GetPositions(operations_pb2.PositionsRequest(account_id=account_id))
        # print(positions_stub)
        # self.get_portfolio(account_id)
        # return portfolio_stub.positions

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
