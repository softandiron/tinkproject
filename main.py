# TinkProject
# developed by.. sorry, I should stay anonymous for my security.
# my nickname: softandiron
# Moscow 2021

import logging
import sys
import time
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal
import operator
import scipy.optimize

import data_parser
from excel_builder import build_excel_file, supported_currencies


@dataclass
class PortfolioPosition:
    figi: str
    name: str
    ticker: str
    balance: Decimal
    position_type: str
    currency: Decimal
    ave_price: Decimal
    sum_buy: Decimal
    exp_yield: Decimal
    market_price: Decimal
    percent_change: Decimal
    market_cost: Decimal
    market_value_rub: Decimal
    market_cost_rub_cb: Decimal
    ave_buy_price_rub: Decimal
    sum_buy_rub: Decimal
    tax_base: Decimal
    exp_tax: Decimal


@dataclass
class PortfolioOperation:
    op_type: str
    op_date: str
    op_currency: str
    op_payment: Decimal
    op_ticker: str


def get_portfolio_cash_rub():
    for cur in currencies.payload.currencies:
        if cur.currency == 'RUB':
            return cur.balance
    return 0


# tax calculation
def calculate_ave_buy_price_rub(this_pos):
    item_list = []
    # for this position's figi - add units into the list from operations
    for ops in reversed(operations.payload.operations):
        date = datetime.date(ops.date)
        rate_for_date = rates_CB[date]

        if ops.figi == this_pos.figi and ops.payment != 0:
            if ops.operation_type == 'Buy':
                if ops.currency in supported_currencies:
                    # price for 1 item
                    item = (ops.payment / ops.quantity_executed) * rate_for_date[ops.currency]
                    # add bought items to the list:
                    item_list += [item] * ops.quantity_executed
                else:
                    logger.warning('unknown currency in position: ' + this_pos.name)
            elif ops.operation_type == 'Sell':
                # remove sold items from the list:
                number = ops.quantity_executed
                del item_list[:number]

        # solving problem with TCSG stocks:
        if this_pos.figi == 'BBG00QPYJ5H0':
            if ops.figi == 'BBG005DXJS36' and ops.payment != 0:
                if ops.operation_type == 'Buy':
                    if ops.currency == 'RUB':
                        # price for 1 item
                        item = ops.payment / ops.quantity_executed
                        # add bought items to the list:
                        item_list += [item] * ops.quantity_executed
                    else:
                        logger.warning('unknown currency in position: ' + this_pos.name)
                elif ops.operation_type == 'Sell':
                    # remove sold items from the list:
                    number = ops.quantity_executed
                    del item_list[:number]

    # calculate average buying price in Rub
    ave_buy_price_rub = 0
    if len(item_list) != 0:
        ave_buy_price_rub = sum(item_list) / len(item_list)

    return abs(ave_buy_price_rub)


def creating_positions_objects():
    logger.info('creating position objects..')

    number_positions = len(positions.payload.positions)
    logger.info(f'{number_positions} positions in portfolio')
    number_operations = len(operations.payload.operations)
    logger.info(f'{number_operations} operations in period')

    my_positions = list()
    for this_pos in positions.payload.positions:
        # type (stock, bond, etf or currency)
        position_type = data_parser.get_position_type(this_pos.figi).value

        if this_pos.average_position_price.value > 0:
            if position_type == "Bond":
                # market cost (total for each position)
                market_cost = round((this_pos.expected_yield.value + (this_pos.average_position_price.value *
                                                                      this_pos.balance)), 2)
                # current market prise for 1 item
                market_price = round((market_cost / this_pos.balance), 2)
            else:
                # current market prise for 1 item
                market_price = data_parser.get_current_market_price(this_pos.figi)
                # market cost (total for each position)
                market_cost = market_price * this_pos.balance

            # % change
            percent_change = ((market_price / this_pos.average_position_price.value) * 100) - 100

            # market value RUB (total cost for each position)
            market_value_rub = market_cost * market_rate_today[this_pos.average_position_price.currency]

            global market_cost_rub_cb
            # total value rub CB
            if this_pos.average_position_price.currency in supported_currencies:
                market_cost_rub_cb = market_cost * rates_CB[today_date][this_pos.average_position_price.currency]
            else:
                market_cost_rub_cb = 'unknown currency'

            # sum buy (purchase amount)

            sum_buy = this_pos.average_position_price.value * this_pos.balance

            ave_buy_price_rub = calculate_ave_buy_price_rub(this_pos)
            sum_buy_rub = ave_buy_price_rub * this_pos.balance

            tax_base = Decimal(max(0, market_cost_rub_cb - sum_buy_rub))
            exp_tax = tax_base * Decimal(tax_rate / 100)

            logger.info(this_pos.name)

        else:  # in the case, if this position has ZERO purchase price
            sum_buy = Decimal(0)
            market_price = data_parser.get_current_market_price(this_pos.figi)
            percent_change = Decimal(0)
            market_cost = market_price * this_pos.balance
            market_value_rub = market_cost * market_rate_today[this_pos.average_position_price.currency]
            market_cost_rub_cb = Decimal(0)
            ave_buy_price_rub = Decimal(0)
            sum_buy_rub = Decimal(0)
            tax_base = Decimal(0)
            exp_tax = Decimal(0)
            logger.warning(this_pos.name + ' - not enough data!')

        my_positions.append(PortfolioPosition(this_pos.figi, this_pos.name, this_pos.ticker, this_pos.balance,
                                              position_type, this_pos.average_position_price.currency,
                                              this_pos.average_position_price.value, sum_buy,
                                              this_pos.expected_yield.value,
                                              market_price, percent_change, market_cost, market_value_rub,
                                              market_cost_rub_cb, ave_buy_price_rub, sum_buy_rub, tax_base, exp_tax))

    my_positions.sort(key=operator.attrgetter('name'))
    logger.info('..positions are ready')
    return my_positions


def get_average_percent():
    sum_buy_list, yield_list = [], []
    for this_pos in my_positions:
        if this_pos.currency in supported_currencies:
            sum_buy_list.append(this_pos.sum_buy * market_rate_today[this_pos.currency])
            yield_list.append(this_pos.exp_yield * market_rate_today[this_pos.currency])
        else:
            logger.warning(f'Unsupported currency: {this_pos.currency}')
    return (sum(yield_list) / sum(sum_buy_list)) * 100


def get_portfolio_cost_rub_market():
    costs_list = []
    for this_pos in my_positions:
        if this_pos.currency in supported_currencies:
            costs_list.append(this_pos.market_cost * market_rate_today[this_pos.currency])
        else:
            logger.warning(f'Unsupported currency: {this_pos.currency}')
    return sum(costs_list) + cash_rub


def calculate_cb_value_rub_sum():
    return sum(pos.market_cost_rub_cb for pos in my_positions) + cash_rub


def calculate_sum_pos_ave_buy_rub():
    return sum(pos.sum_buy_rub for pos in my_positions)


def calculate_sum_exp_tax():
    return sum(pos.exp_tax for pos in my_positions)


def create_operations_objects():
    logger.info('creating operations objects..')
    my_operations = list()
    instruments_dictionary = {}
    for this_op in operations.payload.operations:
        if this_op.figi != None:
            if this_op.figi not in instruments_dictionary:
                instrument = data_parser.get_instrument_by_figi(this_op.figi)
                ticker = instrument.payload.ticker
                instruments_dictionary[this_op.figi] = ticker
            else:
                ticker = instruments_dictionary[this_op.figi]
        else:
            ticker = "None"

        my_operations.append(PortfolioOperation(this_op.operation_type,
                                                this_op.date,
                                                this_op.currency,
                                                this_op.payment,
                                                ticker))

    logger.info('..operations are ready')
    return my_operations


def calculate_operations_sums_rub(current_op_type):
    op_list = []
    for op in my_operations:
        if op.op_type == current_op_type and op.op_payment != 0:
            if op.op_currency in supported_currencies:
                date = datetime.date(op.op_date)  # op_date has a datetime.datetime type. I don't know, what a problem.
                rate = rates_CB[date]
                op_list.append(op.op_payment * rate[op.op_currency])
            else:
                logger.warning(f'Unsupported currency: {op.op_currency}')
    return sum(op_list)


def xnpv(valuesPerDate, rate):
    # Calculate the irregular net present value.
    days_per_year = 365.0

    if rate == -1.0:
        return float('inf')

    t0 = min(valuesPerDate.keys())

    if rate <= -1.0:
        return sum([-abs(vi) / (-1.0 - rate)**((ti - t0).days / days_per_year) for ti, vi in valuesPerDate.items()])

    return sum([vi / (1.0 + rate)**((ti - t0).days / days_per_year) for ti, vi in valuesPerDate.items()])


def xirr(valuesPerDate):
    # Calculate the irregular internal rate of return
    if not valuesPerDate:
        return None

    if all(v >= 0 for v in valuesPerDate.values()):
        return float("inf")
    if all(v <= 0 for v in valuesPerDate.values()):
        return -float("inf")

    result = None
    try:
        result = scipy.optimize.newton(lambda r: xnpv(valuesPerDate, r), 0)
    except (RuntimeError, OverflowError):    # Failed to converge?
        result = scipy.optimize.brentq(lambda r: xnpv(valuesPerDate, r), -0.999999999999999, 1e20, maxiter=10**6)

    if not isinstance(result, complex):
        return result
    else:
        return None


def calculate_xirr(operations, portfolio_value):
    logger.info('calculating XIRR..')
    dates_values = {}
    for op in operations:
        if (op.op_type == 'PayIn' or op.op_type == 'PayOut') and op.op_payment != 0:
            if op.op_currency in supported_currencies:
                date = datetime.date(op.op_date)
                rate = rates_CB[date]
                dates_values[op.op_date] = -(op.op_payment * rate[op.op_currency])  # reverting the sign
            else:
                logger.warning(f'Unsupported currency: {op.op_currency}')

    dates_values_sorted = {}
    for date in sorted(dates_values.keys()):
        dates_values_sorted[date] = int(dates_values[date])

    dates_values_composed = {}
    for date in dates_values_sorted.keys():
        if datetime.date(date) not in dates_values_composed.keys():
            dates_values_composed[datetime.date(date)] = dates_values_sorted[date]
        else:
            dates_values_composed[datetime.date(date)] += dates_values_sorted[date]

    dates_values_composed[datetime.date(data_parser.account_data['now_date'])] = int(portfolio_value)

    x = round((xirr(dates_values_composed) * 100), 2)
    return x


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(asctime)s - %(message)s', datefmt='%H:%M:%S')
    logger = logging.getLogger()
    if sys.argv[-1] in ['-q', '--quiet']:
        logger.setLevel(logging.WARNING)

    start_time = time.time()
    tax_rate = 13  # percents
    logger.info('Start')

    # from data_parser
    positions, operations, market_rate_today, currencies = data_parser.get_api_data(logger)
    account_data = data_parser.parse_text_file(logger)
    today_date = datetime.date(account_data['now_date'])
    investing_period = data_parser.calc_investing_period(logger)
    investing_period_str = f'{investing_period.years}y {investing_period.months}m {investing_period.days}d'
    rates_CB = data_parser.loop_dates(logger)
    rates_today_cb = rates_CB[today_date]

    # from main
    cash_rub = get_portfolio_cash_rub()
    my_positions = creating_positions_objects()
    average_percent = get_average_percent()
    portfolio_cost_rub_market = get_portfolio_cost_rub_market()

    sum_profile = {}
    sum_profile['portfolio_value_rub_cb'] = calculate_cb_value_rub_sum()
    sum_profile['pos_ave_buy_rub'] = calculate_sum_pos_ave_buy_rub()
    sum_profile['exp_tax'] = calculate_sum_exp_tax()

    my_operations = create_operations_objects()

    xirr_value = calculate_xirr(my_operations, (portfolio_cost_rub_market - sum_profile['exp_tax']))

    for operation in ['PayIn', 'PayOut', 'Buy', 'BuyCard', 'Sell', 'Coupon', 'Dividend', 'Tax', 'TaxCoupon',
                      'TaxDividend', 'BrokerCommission', 'ServiceCommission']:
        logger.info(f'calculating {operation} operations sum in RUB..')
        sum_profile[operation.lower()] = calculate_operations_sums_rub(operation)

    logger.info('preparing statistics')

    # PayIn - PayOut
    payin_payout = sum_profile['payin'] - abs(sum_profile['payout'])

    # EXCEL
    build_excel_file(my_positions, my_operations, rates_today_cb, market_rate_today,
                     average_percent, portfolio_cost_rub_market, sum_profile,
                     investing_period_str, cash_rub, payin_payout, xirr_value, logger)

    logger.info(f'done in {time.time() - start_time:.2f} seconds')
