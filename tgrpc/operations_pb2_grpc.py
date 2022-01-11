# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import tgrpc.operations_pb2 as operations__pb2


class OperationsServiceStub(object):
    """Сервис предназначен для получения:</br> **1**.  списка операций по счёту;</br> **2**.
    портфеля по счёту;</br> **3**. позиций ценных бумаг на счёте;</br> **4**.
    доступного остатка для вывода средств.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetOperations = channel.unary_unary(
                '/tinkoff.public.invest.api.contract.v1.OperationsService/GetOperations',
                request_serializer=operations__pb2.OperationsRequest.SerializeToString,
                response_deserializer=operations__pb2.OperationsResponse.FromString,
                )
        self.GetPortfolio = channel.unary_unary(
                '/tinkoff.public.invest.api.contract.v1.OperationsService/GetPortfolio',
                request_serializer=operations__pb2.PortfolioRequest.SerializeToString,
                response_deserializer=operations__pb2.PortfolioResponse.FromString,
                )
        self.GetPositions = channel.unary_unary(
                '/tinkoff.public.invest.api.contract.v1.OperationsService/GetPositions',
                request_serializer=operations__pb2.PositionsRequest.SerializeToString,
                response_deserializer=operations__pb2.PositionsResponse.FromString,
                )
        self.GetWithdrawLimits = channel.unary_unary(
                '/tinkoff.public.invest.api.contract.v1.OperationsService/GetWithdrawLimits',
                request_serializer=operations__pb2.WithdrawLimitsRequest.SerializeToString,
                response_deserializer=operations__pb2.WithdrawLimitsResponse.FromString,
                )


class OperationsServiceServicer(object):
    """Сервис предназначен для получения:</br> **1**.  списка операций по счёту;</br> **2**.
    портфеля по счёту;</br> **3**. позиций ценных бумаг на счёте;</br> **4**.
    доступного остатка для вывода средств.
    """

    def GetOperations(self, request, context):
        """Метод получения списка операций по счёту
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetPortfolio(self, request, context):
        """Метод получения портфеля по счёту
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetPositions(self, request, context):
        """Метод получения списка позиций по счёту
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetWithdrawLimits(self, request, context):
        """Метод получения доступного остатка для вывода средств
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_OperationsServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetOperations': grpc.unary_unary_rpc_method_handler(
                    servicer.GetOperations,
                    request_deserializer=operations__pb2.OperationsRequest.FromString,
                    response_serializer=operations__pb2.OperationsResponse.SerializeToString,
            ),
            'GetPortfolio': grpc.unary_unary_rpc_method_handler(
                    servicer.GetPortfolio,
                    request_deserializer=operations__pb2.PortfolioRequest.FromString,
                    response_serializer=operations__pb2.PortfolioResponse.SerializeToString,
            ),
            'GetPositions': grpc.unary_unary_rpc_method_handler(
                    servicer.GetPositions,
                    request_deserializer=operations__pb2.PositionsRequest.FromString,
                    response_serializer=operations__pb2.PositionsResponse.SerializeToString,
            ),
            'GetWithdrawLimits': grpc.unary_unary_rpc_method_handler(
                    servicer.GetWithdrawLimits,
                    request_deserializer=operations__pb2.WithdrawLimitsRequest.FromString,
                    response_serializer=operations__pb2.WithdrawLimitsResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'tinkoff.public.invest.api.contract.v1.OperationsService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class OperationsService(object):
    """Сервис предназначен для получения:</br> **1**.  списка операций по счёту;</br> **2**.
    портфеля по счёту;</br> **3**. позиций ценных бумаг на счёте;</br> **4**.
    доступного остатка для вывода средств.
    """

    @staticmethod
    def GetOperations(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/tinkoff.public.invest.api.contract.v1.OperationsService/GetOperations',
            operations__pb2.OperationsRequest.SerializeToString,
            operations__pb2.OperationsResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetPortfolio(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/tinkoff.public.invest.api.contract.v1.OperationsService/GetPortfolio',
            operations__pb2.PortfolioRequest.SerializeToString,
            operations__pb2.PortfolioResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetPositions(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/tinkoff.public.invest.api.contract.v1.OperationsService/GetPositions',
            operations__pb2.PositionsRequest.SerializeToString,
            operations__pb2.PositionsResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetWithdrawLimits(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/tinkoff.public.invest.api.contract.v1.OperationsService/GetWithdrawLimits',
            operations__pb2.WithdrawLimitsRequest.SerializeToString,
            operations__pb2.WithdrawLimitsResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
