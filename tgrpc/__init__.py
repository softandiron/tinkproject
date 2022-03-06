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
                           FutureMargin,
                           Instrument,
                           INSTRUMENT_ID_TYPE,
                           MoneyAmmount,
                           Operation,
                           PortfolioPosition,
                           Price,  # Quotation from grpc
                           )
import tgrpc.service as service

from google.protobuf.timestamp_pb2 import Timestamp

from typing import List, Union, Callable, Any, TypeVar

logger = logging.getLogger("tgrpc")

RATE_LIMIT_TIMEOUT = 5  # seconds


class tgrpc_parser():

    token = ""
    api_endpoint = "invest-public-api.tinkoff.ru:443"

    channel = None

    DEBUG_IDS = []

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

    def _debug_ids(func):
        # decorator to debug Figis and Tickers
        def wrapper(self, *args, **kwargs):
            # если есть запросы к figi/ticker из списка для дебага в аргументах функции,
            # выставить временный уровень логов на DEBUG
            def_log_level = logging.getLogger().level
            if len(self.DEBUG_IDS) > 0:
                for id in self.DEBUG_IDS:
                    if id in args or id in kwargs.values():
                        logging.getLogger().setLevel(logging.DEBUG)
                        break

            return_val = func(self, *args, **kwargs)

            logging.getLogger().setLevel(def_log_level)
            return return_val
        return wrapper

    def _catch_grpc_error(func):
        # Decorator function to catch GRPC errors
        def wrapper(self, *args, **kwargs):
            # чтобы можно было повторить вызов, если ошибка в количестве запросов.
            while True:
                try:
                    return func(self, *args, **kwargs)
                except grpc.RpcError as rpc_error:
                    error_code = rpc_error.code()
                    if error_code == grpc.StatusCode.RESOURCE_EXHAUSTED:
                        logger.warning(f"Rate limit in {func.__name__} -> Timeout {RATE_LIMIT_TIMEOUT}s")
                        time.sleep(RATE_LIMIT_TIMEOUT)
                        # не возвращает значение, поскольку должно пойти на повтор запроса к API
                    elif error_code == grpc.StatusCode.UNAUTHENTICATED:
                        logger.error("Authentication failure!")
                        logger.critical("Token incorrect!")
                        return None
                    elif error_code == grpc.StatusCode.INTERNAL:
                        logger.critical("Tinkoff API internal error")
                        logger.error(f"during function {func.__name__}")
                        logger.error(rpc_error)
                        return None
                    else:
                        logger.error(f"Got GRPC error in {func.__name__}")
                        logger.error(rpc_error)
                        logger.error(error_code.__str__())
                        return None
                except Exception as e:
                    logger.error(f"Got error in {func.__name__}")
                    logger.error(e)
                    return None
        return wrapper

    @_catch_grpc_error
    def get_accounts_list(self) -> List[Account]:
        stub = users_pb2_grpc.UsersServiceStub(self.get_channel())
        accounts_stub = stub.GetAccounts(users_pb2.GetAccountsRequest())
        accounts_list = []
        for account in accounts_stub.accounts:
            opened_date = account.opened_date.ToDatetime()
            closed_date = account.closed_date.ToDatetime()
            accounts_list.append(Account(account.id, account.name, opened_date,
                                         closed_date, account.type, account.status))
        return accounts_list

    @_debug_ids
    @_catch_grpc_error
    def get_candles_raw(self, 
                        figi:str,
                        start_date:datetime,
                        end_date:datetime,
                        interval:CANDLE_INTERVALS = CANDLE_INTERVALS.DAY):
        """Возвращает сырые данные о свечах из API

        Args:
            figi (str): Figi инструмента
            start_date (DateTime): начало запрашиваемого периода
            end_date (DateTime): конец запрашиваемого периода
            interval (CANDLE_INTERVALS, optional): Интервал агрегации данных свечей.
                                                   Defaults to CANDLE_INTERVALS.DAY.
        Returns:
            Массив свечей
        """
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
        return candles_stub.candles

    @_debug_ids
    def get_candles(self, figi, start_date, end_date, interval=CANDLE_INTERVALS.DAY):
        """Возвращает данные о свечах с коррекцией
        на цену номинала Облигации и фьючерса
        TODO: реализовать расчет цены фьючерса

        Args:
            figi (str): Figi инструмента
            start_date (DateTime): начало запрашиваемого периода
            end_date (DateTime): конец запрашиваемого периода
            interval (CANDLE_INTERVALS, optional): Интервал агрегации данных свечей.
                                                   Defaults to CANDLE_INTERVALS.DAY.
        Returns:
            Массив свечей
        """
        candles = self.get_candles_raw(figi, start_date, end_date, interval)
        logger.debug(candles)

        instrument = self.get_instrument_raw(figi)
        instrument_type = instrument.instrument_type
        if instrument_type.lower() == "bond":
            full_instrument = self.get_instrument_raw(figi, instrument_type=instrument_type)
            nominal = MoneyAmmount.fromMoneyAmmount(full_instrument.nominal).ammount
        if instrument_type.lower() == "futures":
            margins = self.get_future_margin(figi)
            min_price_increment = margins.min_price_increment
            min_price_increment_amount = margins.min_price_increment_amount
        candles_out = []
        for candle in candles:
            if instrument_type.lower() == "bond":
                candles_out.append(Candle.bond_candle_from_api(candle, nominal))
            elif instrument_type.lower() == "futures":
                candles_out.append(Candle.futures_candle_from_api(candle,
                                                                  min_price_increment,
                                                                  min_price_increment_amount))
            else:
                candles_out.append(Candle.from_api(candle))
        return candles_out

    @_debug_ids
    def get_currencies(self, account_id:str) -> List[Currency]:
        money = self.get_positions(account_id).money
        currencies = []
        for currency in money:
            currencies.append(Currency(currency))
        return currencies

    @_debug_ids
    @_catch_grpc_error
    def get_future_margin(self, figi):
        stub = instruments_pb2_grpc.InstrumentsServiceStub(self.get_channel())
        request = instruments_pb2.GetFuturesMarginRequest(figi=figi)
        result = stub.GetFuturesMargin(request)

        logger.debug(result)
        return FutureMargin.from_api(result)

    @_debug_ids
    @_catch_grpc_error
    def get_instrument_raw(self, id:str,
                           id_type:INSTRUMENT_ID_TYPE=INSTRUMENT_ID_TYPE.Figi,
                           instrument_type:Union[str, None]=None,
                           class_code:Union[str, None]=None):
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
        elif instrument_type.lower() == "futures":
            logger.debug(f"Get Future {id}")
            result = stub.FutureBy(request)
        else:
            logger.warning(f"Задан неизвестный тип инструмента: {instrument_type}")
            logger.warning(f"Get base data on instrument {id}")
            result = stub.GetInstrumentBy(request)

        logger.debug(result)
        return result.instrument

    @_debug_ids
    def get_instrument(self, id:str,
                       id_type:INSTRUMENT_ID_TYPE=INSTRUMENT_ID_TYPE.Figi,
                       instrument_type:Union[str,None]=None,
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

    @_debug_ids
    @_catch_grpc_error
    def get_last_price_raw(self, figis):
        """Возвращает текущую 'сырую' цену по одному или списку Figi
        Не корректирует на номинал облигации и фьючерса,
        для облигации возвращает процент от номинала,
        для фьючерсов - индекс от номинала

        Args:
            figi (str): запрашиваемый Figi

        Returns:
            Dict: {"figi": Decimal(price),...} цена на запрашиваемые Figi
        """
        if isinstance(figis, str):
            figis = [figis, ]

        stub = marketdata_pb2_grpc.MarketDataServiceStub(self.get_channel())

        price_stub = stub.GetLastPrices(marketdata_pb2.GetLastPricesRequest(figi=figis))

        prices_out = {}
        for position in price_stub.last_prices:
            prices_out[position.figi] = Price.fromQuotation(position.price).ammount
        return prices_out

    @_debug_ids
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
        raw_price = raw_price[figi]
        if instrument_type is None:
            instrument = self.get_instrument_raw(figi, id_type=INSTRUMENT_ID_TYPE.Figi)
            instrument_type = instrument.instrument_type
        if instrument_type.lower() == "bond":
            return self._bond_price_calculation(raw_price, figi)
        elif instrument_type.lower() == "futures":
            return self.futures_price_calculation(raw_price, figi)

        # если не требуется специфического расчета (для акций и етф, например)
        return raw_price

    @_debug_ids
    @_catch_grpc_error
    def get_operations(self, account_id:str,
                       start_date:datetime=datetime(2020, 11, 1, 0, 0),
                       end_date:datetime=datetime.now(tz=timezone.utc),
                       state="",
                       figi:Union[str, None]=None):
        # TODO: реализовать фильтр по статусу операции
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

    @_debug_ids
    @_catch_grpc_error
    def get_positions(self, account_id:str):
        stub = operations_pb2_grpc.OperationsServiceStub(self.get_channel())
        positions_stub = stub.GetPositions(operations_pb2.PositionsRequest(account_id=account_id))
        return positions_stub

    @_debug_ids
    @_catch_grpc_error
    def get_portfolio(self, account_id:str):
        stub = operations_pb2_grpc.OperationsServiceStub(self.get_channel())
        portfolio_stub = stub.GetPortfolio(operations_pb2.PortfolioRequest(account_id=account_id))
        # print(portfolio_stub.positions)
        portfolio_out = []
        for position in portfolio_stub.positions:
            portfolio_out.append(
                PortfolioPosition.from_api(position)
            )
        return portfolio_out

    @_debug_ids
    def _bond_price_calculation(self, raw_price, figi):
        """Расчет реальной цены облигации в валюте

        Args:
            raw_price (Decimal): цена в процентах номинала
            figi (str): идентификатор необходимой облигации

        Returns:
            Decimal: цена в валюте облигации
        """
        # https://tinkoff.github.io/investAPI/faq_marketdata/#_4
        logger.debug("Calculate True Bond price")
        full_instrument = self.get_instrument_raw(figi,
                                                  id_type=INSTRUMENT_ID_TYPE.Figi,
                                                  instrument_type="bond")
        nominal = MoneyAmmount.fromMoneyAmmount(full_instrument.nominal).ammount
        price = service.bond_price_calculation(raw_price, nominal)
        return price

    @_debug_ids
    def futures_price_calculation(self, raw_price, figi):
        """Расчет реальной цены фьчерсов в валюте

        Args:
            raw_price (Decimal): цена в пунктах
            figi (str): идентификатор необходимого фьючерса

        Returns:
            Decimal: цена в валюте фьчерса
        """
        logger.debug("Calculate True Future price")

        margin = self.get_future_margin(figi)
        min_price_increment = margin.min_price_increment
        min_price_increment_amount = margin.min_price_increment_amount

        price = service.futures_price_calculation(raw_price,
                                                  min_price_increment,
                                                  min_price_increment_amount)
        logger.debug(price)
        return Decimal(price)
