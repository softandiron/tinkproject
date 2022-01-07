import logging
import grpc
import tgrpc.users_pb2 as users_pb2
import tgrpc.users_pb2_grpc as users_pb2_grpc
import tgrpc.operations_pb2 as operations_pb2
import tgrpc.operations_pb2_grpc as operations_pb2_grpc
import tgrpc.instruments_pb2 as instruments_pb2

import tgrpc.instruments_pb2_grpc as instruments_pb2_grpc

from tgrpc.classes import Account, PortfolioPosition, INSTRUMENT_ID_TYPE, INSTRUMENT_TYPE

import json
from google.protobuf.json_format import MessageToJson
from google.protobuf.json_format import MessageToDict

logger = logging.getLogger("tgrpc")

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
        logger.info(instrument_type)
        try:
            if instrument_type.lower() in ["share", "stock"]:  # TODO: stock - убрать после - оставлено для обратной совместимости.
                logger.info("Get Share")
                result = stub.ShareBy(request)
            elif instrument_type.lower() == "bond":
                logger.info("Get Bond")
                result = stub.BondBy(request)
            elif instrument_type.lower() == "etf":
                logger.info("Get Etf")
                result = stub.EtfBy(request)
            elif instrument_type.lower() == "currency":
                logger.info("Get Currency {id}")
                result = stub.EtfBy(request)
            elif instrument_type.lower() == "future":
                logger.info("Get Future {id}")
                result = stub.FutureBy(request)
        except Exception as e:
            logger.info(f"{id} - not found")
            logger.info(e)
            return None
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
