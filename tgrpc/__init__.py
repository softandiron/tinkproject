import logging
import time

import grpc

import tgrpc.instruments_pb2 as instruments_pb2
import tgrpc.instruments_pb2_grpc as instruments_pb2_grpc
import tgrpc.operations_pb2 as operations_pb2
import tgrpc.operations_pb2_grpc as operations_pb2_grpc
import tgrpc.instruments_pb2 as instruments_pb2

import tgrpc.instruments_pb2_grpc as instruments_pb2_grpc

from tgrpc.classes import Account, PortfolioPosition, INSTRUMENT_ID_TYPE, INSTRUMENT_TYPE

import json
from google.protobuf.json_format import MessageToJson
from google.protobuf.json_format import MessageToDict

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
        
        logger.debug(result.instrument)
        logger.debug(f"Got instrument {result.instrument.name} - {result.instrument.figi}")
        return result.instrument

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
