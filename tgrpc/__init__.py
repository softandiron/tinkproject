import grpc
import tgrpc.users_pb2 as users_pb2
import tgrpc.users_pb2_grpc as users_pb2_grpc
import tgrpc.operations_pb2 as operations_pb2
import tgrpc.operations_pb2_grpc as operations_pb2_grpc

from tgrpc.classes import Account, PortfolioPosition

import json
from google.protobuf.json_format import MessageToJson
from google.protobuf.json_format import MessageToDict


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
