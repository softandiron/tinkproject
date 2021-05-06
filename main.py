# TinkProject
# developed by.. sorry, I should stay anonymous for my security.
# my nickname: softandiron
# Moscow 2021

from pycbrf.toolbox import ExchangeRates
import time
import datetime
import excel_builder
from dateutil.relativedelta import relativedelta
from decimal import Decimal

import data_parser

delay_time = 0.2
tax_rate = 13  # percents

print('START')

positions, operations, market_rate_today_usd, market_rate_today_eur, currencies = data_parser.get_api_data()

# data_parser.account_data: ['my_token'], ['my_timezone'], ['start_date'], ['now_date']

rates_today_cb = ExchangeRates(data_parser.account_data['now_date'])


def get_portfolio_cash_rub():
    for cur in currencies.payload.currencies:
        if cur.currency == 'RUB':
            return cur.balance


cash_rub = get_portfolio_cash_rub()


class PortfolioPosition:
    def __init__(self, figi, name, ticker, balance, currency, ave_price, exp_yield, market_price, percent_change,
                 market_cost, market_cost_rub_cb, ave_buy_price_rub, sum_buy_rub, tax_base, exp_tax):
        self.figi = figi
        self.name = name
        self.ticker = ticker
        self.balance = balance
        self.currency = currency
        self.ave_price = ave_price
        self.exp_yield = exp_yield
        self.market_price = market_price
        self.percent_change = percent_change
        self.market_cost = market_cost
        self.market_cost_rub_cb = market_cost_rub_cb
        self.ave_buy_price_rub = ave_buy_price_rub
        self.sum_buy_rub = sum_buy_rub
        self.tax_base = tax_base
        self.exp_tax = exp_tax


def creating_positions_objects():
    print('creating position objects..')

    number_positions = len(positions.payload.positions)
    print(str(number_positions) + ' positions in portfolio')
    number_operations = len(operations.payload.operations)
    print(str(number_operations) + ' operations in period')

    my_positions = list()
    for this_pos in positions.payload.positions:
        # market cost (total for each position)
        market_cost = this_pos.expected_yield.value + (this_pos.average_position_price.value * this_pos.balance)

        # current market prise for 1 item
        market_price = market_cost / this_pos.balance

        # % change
        percent_change = ((market_price / this_pos.average_position_price.value) * 100) - 100

        global market_cost_rub_cb
        # market value rub CB
        if this_pos.average_position_price.currency == 'RUB':
            market_cost_rub_cb = market_cost
        elif this_pos.average_position_price.currency == 'USD':
            market_cost_rub_cb = market_cost * rates_today_cb['USD'].value
            time.sleep(delay_time)  # to prevent TimeOut error
        elif this_pos.average_position_price.currency == 'EUR':
            market_cost_rub_cb = market_cost * rates_today_cb['EUR'].value
            time.sleep(delay_time)  # to prevent TimeOut error
        else:
            market_cost_rub_cb = 'unknown currency'

        # for further tax calculation
        def calculate_ave_buy_price_rub():
            item_list = []
            # for this position's figi - add units into the list from operations
            for ops in reversed(operations.payload.operations):
                if ops.figi == this_pos.figi:
                    if ops.operation_type == 'Buy' and ops.payment != 0:
                        i = 0
                        if ops.currency == 'RUB':
                            # price for 1 item
                            item = ops.payment / ops.quantity_executed
                            # add bought items to the list:
                            number = ops.quantity_executed
                            while i < number:
                                item_list.append(item)
                                i += 1
                        elif ops.currency == 'USD':
                            rate_for_date = ExchangeRates(ops.date)
                            # price for 1 item
                            item = (ops.payment / ops.quantity_executed) * rate_for_date['USD'].value
                            # add bought items to the list:
                            number = ops.quantity_executed
                            while i < number:
                                item_list.append(item)
                                i += 1
                        elif ops.currency == 'EUR':
                            rate_for_date = ExchangeRates(ops.date)
                            # price for 1 item
                            item = (ops.payment / ops.quantity_executed) * rate_for_date['EUR'].value
                            # add bought items to the list:
                            number = ops.quantity_executed
                            while i < number:
                                item_list.append(item)
                                i += 1
                        else:
                            print('ERROR: unknown currency in position: ' + this_pos.name)
                    if ops.operation_type == 'Sell' and ops.payment != 0:
                        # remove sold items to the list:
                        number = ops.quantity_executed
                        del item_list[0:number]
                    time.sleep(delay_time)  # to prevent TimeOut error
            # calculate average buying price in Rub
            ave_buy_price_rub = 0
            
            if len(item_list) != 0:
                sum(item_list) / len(item_list)

            return abs(ave_buy_price_rub)

        ave_buy_price_rub = calculate_ave_buy_price_rub()

        sum_buy_rub = ave_buy_price_rub * this_pos.balance

        tax_base = market_cost_rub_cb - sum_buy_rub
        if tax_base < 0:
            tax_base = 0

        exp_tax = tax_base * Decimal(tax_rate / 100)

        my_positions.append(PortfolioPosition(this_pos.figi, this_pos.name, this_pos.ticker, this_pos.balance,
                                              this_pos.average_position_price.currency,
                                              this_pos.average_position_price.value, this_pos.expected_yield.value,
                                              market_price, percent_change, market_cost, market_cost_rub_cb,
                                              ave_buy_price_rub, sum_buy_rub, tax_base, exp_tax))

        print(this_pos.name)

    print('..positions are ready')
    return my_positions


def get_average_percent():
    percent_list = []
    for this_pos in my_positions:
        percent_list.append(this_pos.percent_change)
    return sum(percent_list) / len(percent_list)


def get_portfolio_cost_rub_market():
    costs_list = []
    for this_pos in my_positions:
        if this_pos.currency == 'RUB':
            costs_list.append(this_pos.market_cost)
        elif this_pos.currency == 'USD':
            costs_list.append(this_pos.market_cost * market_rate_today_usd)
        elif this_pos.currency == 'EUR':
            costs_list.append(this_pos.market_cost * market_rate_today_eur)
        else:
            return 'error'
    return sum(costs_list) + cash_rub


def calculate_cb_value_rub_sum():
    list = []
    for pos in my_positions:
        list.append(pos.market_cost_rub_cb)
    return sum(list) + cash_rub


def calculate_sum_pos_ave_buy_rub():
    buy_list = []
    for pos in my_positions:
        buy_list.append(pos.sum_buy_rub)
    return sum(buy_list)


def calculate_sum_exp_tax():
    exp_tax_list = []
    for pos in my_positions:
        exp_tax_list.append(pos.exp_tax)
    return sum(exp_tax_list)


# PART 2

class PortfolioOperation:
    def __init__(self, op_type, op_date, op_currency, op_payment):
        self.op_type = op_type
        self.op_date = op_date
        self.op_currency = op_currency
        self.op_payment = op_payment


def create_operations_objects():
    print('creating operations objects..')
    my_operations = list()
    for this_op in operations.payload.operations:
        op_type = this_op.operation_type
        op_date = this_op.date
        op_currency = this_op.currency
        op_payment = this_op.payment

        my_operations.append(PortfolioOperation(op_type=op_type, op_date=op_date, op_currency=op_currency,
                                                op_payment=op_payment))

    print('..operations are ready')
    return my_operations


def calculate_operations_sums_rub(current_op_type):
    op_list = []
    for op in my_operations:
        if op.op_type == current_op_type:
            if op.op_payment != 0:
                if op.op_currency == 'RUB':
                    op_list.append(op.op_payment)
                elif op.op_currency == 'USD':
                    rate = ExchangeRates(op.op_date)
                    op_list.append(op.op_payment * rate['USD'].value)
                    time.sleep(delay_time)  # to prevent TimeOut error
                elif op.op_currency == 'EUR':
                    rate = ExchangeRates(op.op_date)
                    op_list.append(op.op_payment * rate['EUR'].value)
                    time.sleep(delay_time)  # to prevent TimeOut error
                else:
                    print('error: unknown currency!')

    return sum(op_list)


my_positions = creating_positions_objects()
average_percent = get_average_percent()
portfolio_cost_rub_market = get_portfolio_cost_rub_market()
sum_portfolio_value_rub_cb = calculate_cb_value_rub_sum()
sum_pos_ave_buy_rub = calculate_sum_pos_ave_buy_rub()
sum_exp_tax = calculate_sum_exp_tax()

my_operations = create_operations_objects()

print('calculating PayIn operations sum in RUB..')
sum_payin = calculate_operations_sums_rub('PayIn')

print('calculating PayOut operations sum in RUB..')
sum_payout = calculate_operations_sums_rub('PayOut')

print('calculating Buy operations sum in RUB..')
sum_buy = calculate_operations_sums_rub('Buy')

print('calculating BuyCard operations sum in RUB..')
sum_buycard = calculate_operations_sums_rub('BuyCard')

print('calculating Sell operations sum in RUB..')
sum_sell = calculate_operations_sums_rub('Sell')

print('calculating Coupon operations sum in RUB..')
sum_coupon = calculate_operations_sums_rub('Coupon')

print('calculating Dividend operations sum in RUB..')
sum_dividend = calculate_operations_sums_rub('Dividend')

print('calculating Tax operations sum in RUB..')
sum_tax = calculate_operations_sums_rub('Tax')

print('calculating TaxCoupon operations sum in RUB..')
sum_taxcoupon = calculate_operations_sums_rub('TaxCoupon')

print('calculating TaxDividend operations sum in RUB..')
sum_taxdividend = calculate_operations_sums_rub('TaxDividend')

print('calculating BrokerCommission operations sum in RUB..')
sum_brokercomission = calculate_operations_sums_rub('BrokerCommission')

print('calculating ServiceCommission operations sum in RUB..')
sum_servicecomission = calculate_operations_sums_rub('ServiceCommission')


# PART 3
print('prepare statistics')


def calc_investing_period():
    start_date = data_parser.account_data['start_date'].replace(tzinfo=None)
    # inv_period = data_parser.account_data['now_date'] - start_date
    inv_period = relativedelta(data_parser.account_data['now_date'], start_date)
    return inv_period

# investing period
investing_period = calc_investing_period()
investing_period_str = str(investing_period.years) + 'y ' + str(investing_period.months) + 'm ' + \
                       str(investing_period.days) + 'd'
print('investing period: ' + investing_period_str)

# PayIn - PayOut
payin_payout = sum_payin - abs(sum_payout)




# EXCEL
excel_builder.build_excel_file(my_positions, my_operations, rates_today_cb, market_rate_today_usd,
                               market_rate_today_eur, average_percent, portfolio_cost_rub_market,
                               sum_portfolio_value_rub_cb, sum_pos_ave_buy_rub, sum_exp_tax,
                               sum_payin, sum_payout, sum_buy, sum_buycard, sum_sell, sum_coupon, sum_dividend,
                               sum_tax, sum_taxcoupon, sum_taxdividend, sum_brokercomission, sum_servicecomission,
                               investing_period_str, cash_rub, payin_payout)

