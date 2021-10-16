# TinkProject
# developed by.. sorry, I should stay anonymous for my security.
# my nickname: softandiron
# Moscow 2021

import logging
import sys
import time
from datetime import datetime
from decimal import Decimal
import operator
import scipy.optimize

from classes import PortfolioOperation, PortfolioPosition

import data_parser

import excel_builder
from excel_builder import build_excel_file, supported_currencies, assets_types


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
        rate_for_date = data_parser.get_exchange_rates_for_date_db(date)

        if ops.figi == this_pos.figi and ops.payment != 0:
            if ops.operation_type == 'Buy' or ops.operation_type == 'BuyCard':
                # Определим - был ли в истории сплит или обратный сплит
                op_price = Decimal(ops.payment / ops.quantity_executed)
                quantity = ops.quantity_executed
                price = data_parser.get_figi_history_price(ops.figi, date)

                logger.debug(f"Цена на {date} на бирже - {price}, в операции - {op_price}")
                logger.debug(f"{ops}")

                if ops.currency != this_pos.average_position_price.currency:
                    # Если валюта расчетов за актив менялась - то не исользвать расчет сплита
                    # Например AMHY и AMIG в августе 2021 года перешли с USD на RUB
                    logger.debug(f"{this_pos.ticker} - произошла смена валют актива! "
                                 f"{ops.currency} -> {this_pos.average_position_price.currency}")
                elif price:
                    # Определяем соотношение цен. Больше 1 - сплит акции, меньше 1 - обратный сплит
                    # соответственно меняем количество купленных бумаг в пропорции
                    ratio = Decimal(abs(op_price/price))
                    logger.debug(f"Отношение цен - {ratio}")
                    if round(ratio) > 1:
                        ratio = round(ratio)
                        logger.warning(f"Вероятно, был сплит {this_pos.ticker} - "
                                       f"отношение цен 1:{ratio}")
                        quantity = int(quantity*ratio)
                    elif round(ratio, 2) < Decimal(0.95):
                        # 0.95 - для погрешности в ценах свечей за день
                        ratio_out = 1/ratio
                        logger.warning(f"Вероятно, был обратный сплит {this_pos.ticker} - "
                                       f"отношение цен {ratio_out:.0f}:1")
                        quantity = int(quantity/ratio)

                # Когда опередлились с количеством активов по заявленной цене - считаем
                if ops.currency in supported_currencies:
                    # price for 1 item
                    item = (ops.payment / quantity) * rate_for_date[ops.currency]
                    # add bought items to the list:
                    item_list += [item] * quantity
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
        this_pos_instrument = data_parser.get_instrument_by_figi(this_pos.figi)
        curr_market_price = data_parser.get_current_market_price(this_pos.figi)

        currency = this_pos.average_position_price.currency
        market_rate = market_rate_today[currency]
        cb_rate = data_parser.get_exchange_rate_db(today_date, currency)

        tmp_position = PortfolioPosition.from_api_data(this_pos, this_pos_instrument,
                                                       curr_market_price,
                                                       market_rate, cb_rate)

        if this_pos.average_position_price.value > 0:
            ave_buy_price_rub = calculate_ave_buy_price_rub(this_pos)
            logger.info(this_pos.name)
        else:  # in the case, if this position has ZERO purchase price
            ave_buy_price_rub = Decimal(0)
            logger.warning(this_pos.name + ' - not enough data!')

        tmp_position.ave_buy_price_rub = ave_buy_price_rub

        my_positions.append(tmp_position)

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


def calculate_profit_sum():
    list = []
    for pos in my_positions:
        if pos.tax_base > 0:
            list.append(pos.tax_base)
    return sum(list)


def calculate_profit_tax():
    return round(sum_profile['profit'] * Decimal(tax_rate / 100), 2)


def calculate_loss_tax():
    return round(sum_profile['loss'] * Decimal(tax_rate / 100), 2)


def calculate_loss_sum():
    list = []
    for pos in my_positions:
        if pos.tax_base < 0:
            list.append(pos.tax_base)
    return sum(list)


def calculate_sum_exp_tax():
    return Decimal(max(0, sum(pos.exp_tax for pos in my_positions)))


def calculate_parts():
    logger.info('calculating parts')
    parts = {'totalValue': cash_rub,
             'RUB': {
                 'Currency': {
                    'value': cash_rub,
                    'valueRub': cash_rub
                    },
                 'value': cash_rub,
                 'valueRub': cash_rub
                 },
             }
    for pos in my_positions:
        currency = pos.currency
        value = pos.market_cost
        if pos.position_type == "Currency":
            value = pos.balance
            if pos.ticker == "USD000UTSTOM":
                currency = "USD"
            elif pos.ticker == "EUR_RUB__TOM":
                currency = "EUR"

        if currency not in parts.keys():
            parts[currency] = {'value': 0,
                               'valueRub': 0}
        if pos.position_type not in parts[currency].keys():
            parts[currency][pos.position_type] = {'value': 0,
                                                  'valueRub': 0}
        if pos.position_type not in parts.keys():
            parts[pos.position_type] = {'valueRub': 0}
        parts[currency][pos.position_type]['value'] += value
        parts[currency][pos.position_type]['valueRub'] += pos.market_cost_rub_cb
        parts[currency]['value'] += value
        parts[currency]['valueRub'] += pos.market_cost_rub_cb
        parts['totalValue'] += pos.market_cost_rub_cb
        parts[pos.position_type]['valueRub'] += pos.market_cost_rub_cb
    for currency in supported_currencies:
        if currency not in parts.keys():
            continue
        data = parts[currency]
        for type in assets_types:
            if type in parts.keys():
                parts[type]['totalPart'] = parts[type]['valueRub']/parts['totalValue'] if parts['totalValue'] > 0 else 0
            if type not in data.keys():
                continue
            type_data = data[type]
            type_data['currencyPart'] = type_data['value']/data['value']*100 if data['value'] > 0 else 0
            type_data['totalPart'] = type_data['valueRub']/parts['totalValue']*100 if parts['totalValue'] > 0 else 0
        data['totalPart'] = data['valueRub']/parts['totalValue'] if parts['totalValue'] > 0 else 0
    return parts


def calculate_iis_deduction():
    """Расчет вычета по счетам ИИС

    Returns:
        None: если счет не ИИС
        Dict: {int(год): {'pay_in': Decimal('взносы'), 'base': Decimal('налоговая база'),
                          'deduct': Decimal('объем вычета')},
               0: Decimal('сумма вычетов за все годы')}
              }
    """
    if sum_profile['broker_account_type'] != "TinkoffIis":
        logger.debug("account is not of IIS Type")
        return None
    logger.info("calculating IIS deductions data")

    year_sums = {}
    for operation in my_operations:
        if operation.op_type != 'PayIn':
            continue
        # По состоянию на 08.09.2021 пополнять ИИС можно только рублями,
        # Поэтому проверка формальная на случай - если вдруг это изменится
        operation_year = int(operation.op_date.strftime('%Y'))
        if operation.op_currency != "RUB":
            logger.warning(f"Пополнение ИИС в {operation_year} году не в рублях!")
            logger.warning(operation)
            continue
        if operation_year not in year_sums.keys():
            year_sums[operation_year] = {'pay_in': operation.op_payment}
        else:
            year_sums[operation_year]["pay_in"] += operation.op_payment

    deduct_total = 0
    base_limit = Decimal(400000)  # Ограничение налоговой базы по закону
    payin_limit = Decimal(1000000)  # Ограничение на взносы за год по закону
    for year in sorted(year_sums.keys(), reverse=True):
        payin = year_sums[year]["pay_in"]
        year_sums[year]["pay_in"] = round(payin, 2)
        if payin > payin_limit:
            # если тут - то где-то что-то пошло ОЧЕНЬ неправильно!
            logger.warning(f'Взносы на ИИС в {year}г. больше лимита на взносы'
                           f' {payin_limit}р и составили {payin}р')
        base = payin
        if payin > base_limit:
            base = base_limit
            logger.info(f'Взносы на ИИС в {year}г. больше лимита на вычет {base_limit}р, '
                        f'составили {payin}р. Налоговая база скорректирована.')
        deduct = round(base * Decimal(0.13), 2)
        year_sums[year]['base'] = base
        year_sums[year]['deduct'] = deduct
        deduct_total += deduct
    year_sums[0] = deduct_total
    logger.debug(year_sums)
    return year_sums


def create_operations_objects():
    logger.info('creating operations objects..')
    my_operations = list()
    for this_op in operations.payload.operations:
        date = datetime.date(this_op.date)
        rate_for_date = data_parser.get_exchange_rates_for_date_db(date)
        # ticker
        if this_op.figi is not None:
            ticker = data_parser.get_ticker_by_figi(this_op.figi)
        else:
            ticker = "None"

        # payment_RUB
        if this_op.currency in supported_currencies:
            payment_rub = this_op.payment * rate_for_date[this_op.currency]
        else:
            logger.warning('unknown currency in position: ' + this_op.name)
            payment_rub = 0

        my_operations.append(PortfolioOperation(this_op.operation_type,
                                                this_op.date,
                                                this_op.currency,
                                                this_op.payment,
                                                ticker, payment_rub,
                                                this_op.figi))

    logger.info('..operations are ready')
    return my_operations


def calculate_operations_sums_rub(current_op_type):
    op_list = []
    for op in my_operations:
        if op.op_type == current_op_type and op.op_payment != 0:
            if op.op_currency in supported_currencies:
                date = datetime.date(op.op_date)  # op_date has a datetime.datetime type. I don't know, what is a problem.
                rate_for_date = data_parser.get_exchange_rates_for_date_db(date)
                op_list.append(op.op_payment * rate_for_date[op.op_currency])
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
    except (RuntimeError, OverflowError, ValueError):    # Failed to converge?
        pass
    except Exception as e:
        logger.error(f"XIRR - unknown exception during calculation: {e}")

    if not result:
        logger.info("XIRR - trying another method of calculation")
        try:
            result = scipy.optimize.brentq(lambda r: xnpv(valuesPerDate, r), -0.999999999999999, 1e20, maxiter=10**6)
        except Exception as e:
            logger.warning(f"Could not calculate XIRR: {e}")

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
                rate_for_date = data_parser.get_exchange_rates_for_date_db(date)
                dates_values[op.op_date] = -(op.op_payment * rate_for_date[op.op_currency])  # reverting the sign
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

    xirr_value = xirr(dates_values_composed)
    if xirr_value:
        x = round((xirr_value * 100), 2)
    else:
        x = "---"
    return x


if __name__ == '__main__':

    logging_level = logging.INFO

    if sys.argv[-1] in ['-q', '--quiet']:
        logging_level = logging.WARNING
    elif sys.argv[-1] in ['-d', '--debug']:
        logging_level = logging.DEBUG

    logging.basicConfig(level=logging_level,
                        format='%(asctime)s [%(levelname)-3s] %(name)s: %(message)s',
                        datefmt='%H:%M:%S')
    logger = logging.getLogger()
    data_parser.logger.setLevel(logging_level)
    excel_builder.logger.setLevel(logging_level)

    start_time = time.time()
    tax_rate = 13  # percents
    logger.info('Start')

    # get accounts
    accounts = data_parser.get_accounts()
    for account in accounts.payload.accounts:
        logger.info(account)

        # from data_parser
        positions, operations, market_rate_today, currencies = data_parser.get_api_data(account.broker_account_id)
        account_data = data_parser.parse_text_file()
        today_date = datetime.date(account_data['now_date'])
        investing_period = data_parser.calc_investing_period()
        investing_period_str = f'{investing_period.years}y {investing_period.months}m {investing_period.days}d'
        rates_today_cb = data_parser.get_exchange_rates_for_date_db(today_date)

        # from main
        cash_rub = get_portfolio_cash_rub()
        my_positions = creating_positions_objects()
        average_percent = get_average_percent()
        portfolio_cost_rub_market = get_portfolio_cost_rub_market()

        sum_profile = {}
        sum_profile['broker_account_type'] = account.broker_account_type.value
        sum_profile['portfolio_value_rub_cb'] = calculate_cb_value_rub_sum()
        sum_profile['pos_ave_buy_rub'] = calculate_sum_pos_ave_buy_rub()
        sum_profile['exp_tax'] = calculate_sum_exp_tax()
        sum_profile['profit'] = calculate_profit_sum()
        sum_profile['loss'] = calculate_loss_sum()
        sum_profile['profit_tax'] = calculate_profit_tax()
        sum_profile['loss_tax'] = calculate_loss_tax()
        sum_profile['parts'] = calculate_parts()

        my_operations = create_operations_objects()

        sum_profile['iis_deduction'] = calculate_iis_deduction()

        xirr_value = calculate_xirr(my_operations, (portfolio_cost_rub_market - sum_profile['exp_tax']))

        for operation in ['PayIn', 'PayOut', 'Buy', 'BuyCard', 'Sell', 'Coupon', 'Dividend',
                          'Tax', 'TaxCoupon', 'TaxDividend',
                          'BrokerCommission', 'ServiceCommission']:
            logger.info(f'calculating {operation} operations sum in RUB..')
            sum_profile[operation.lower()] = calculate_operations_sums_rub(operation)

        logger.info('preparing statistics')

        # PayIn - PayOut
        payin_payout = sum_profile['payin'] - abs(sum_profile['payout'])

        # EXCEL
        build_excel_file(account, my_positions, my_operations, rates_today_cb, market_rate_today,
                         average_percent, portfolio_cost_rub_market, sum_profile,
                         investing_period_str, cash_rub, payin_payout, xirr_value, tax_rate)

    logger.info(f'done in {time.time() - start_time:.2f} seconds')
