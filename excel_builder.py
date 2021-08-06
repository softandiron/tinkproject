# Creating and filling an Excel file

import logging
import xlsxwriter
import data_parser

supported_currencies = ['RUB', 'USD', 'EUR']


def get_color(num):
    if num > 0:
        return 'green'
    if num < 0:
        return 'red'
    return 'black'


def build_excel_file(my_positions, my_operations, rates_today_cb, market_rate_today,
                     average_percent, portfolio_cost_rub_market, sum_profile,
                     investing_period_str, cash_rub, payin_payout, xirr_value, tax_rate, logger=logging.getLogger()):

    logger.info('creating excel file..')
    excel_file_name = 'tinkoffReport_' + data_parser.account_data['now_date'].strftime('%Y.%b.%d') + '.xlsx'
    workbook = xlsxwriter.Workbook(excel_file_name)
    worksheet_port = workbook.add_worksheet("Portfolio")
    worksheet_ops = workbook.add_worksheet("Operations")
    worksheet_divs = workbook.add_worksheet("Coupons and Dividends")

    # styles
    cell_format = {}
    cell_format['center'] = workbook.add_format({'align': 'center'})
    cell_format['right'] = workbook.add_format({'align': 'right'})
    cell_format['left'] = workbook.add_format({'align': 'left'})
    cell_format['bold_center'] = workbook.add_format({'align': 'center', 'bold': True})
    cell_format['bold_right'] = workbook.add_format({'align': 'right', 'bold': True})
    cell_format['USD'] = workbook.add_format({'num_format': '## ### ##0.00   [$$-409]', 'align': 'right'})
    cell_format['RUB'] = workbook.add_format({'num_format': '## ### ##0.00   [$₽-ru-RU]', 'align': 'right'})
    cell_format['EUR'] = workbook.add_format({'num_format': '## ### ##0.00   [$€-x-euro1]', 'align': 'right'})
    merge_format = {}
    merge_format['bold_center'] = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True})
    merge_format['bold_right'] = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bold': True})
    merge_format['bold_left'] = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True})
    merge_format['left'] = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': False})
    merge_format['left_small'] = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': False, 'font_size': '9'})

    worksheet_port.set_column('A:A', 16)
    worksheet_port.write(0, 0, data_parser.account_data['now_date'].strftime('%Y %b %d  %H:%M'), cell_format['bold_center'])

    def print_portfolio(s_row, s_col):
        logger.info('building portfolio table..')
        s_row += 3

        def set_columns_width():
            logger.info('setting column width..')
            worksheet_port.set_column(s_col, s_col, 28)  # name
            worksheet_port.set_column(s_col + 1, s_col + 1, 14)  # ticker
            worksheet_port.set_column(s_col + 2, s_col + 2, 12)  # balance
            worksheet_port.set_column(s_col + 3, s_col + 3, 8)  # currency
            worksheet_port.set_column(s_col + 4, s_col + 4, 12)  # ave.price
            worksheet_port.set_column(s_col + 5, s_col + 5, 14)  # sum.buy
            worksheet_port.set_column(s_col + 6, s_col + 6, 14)  # exp.yield
            worksheet_port.set_column(s_col + 7, s_col + 7, 12)  # market price
            worksheet_port.set_column(s_col + 8, s_col + 8, 10)  # % change
            worksheet_port.set_column(s_col + 9, s_col + 9, 14)  # market value
            worksheet_port.set_column(s_col + 10, s_col + 10, 16)  # market value RUB

            worksheet_port.set_column(s_col + 12, s_col + 16, 16)  # CB value RUB

        def build_header():
            logger.info('printing header..')

            for shift, name in enumerate(['name', 'ticker', 'balance', 'currency', 'ave.price', 'sum.buy', 'exp.yield',
                                          'market price', '% change', 'market value', 'market value RUB', '',
                                          'CB value RUB', 'ave.buy in RUB', 'sum.buy in RUB', 'tax base',
                                          'expected tax']):
                worksheet_port.write(s_row, s_col + shift, name, cell_format['bold_center'])

        def build_cb_rate():
            logger.info('printing CB rates..')
            worksheet_port.write(s_row - 3, s_col + 12, 'Central Bank', cell_format['bold_center'])
            worksheet_port.write(s_row - 3, s_col + 13, 'today rates:', cell_format['bold_center'])
            worksheet_port.write(s_row - 2, s_col + 12, f"USD = {rates_today_cb['USD']}", cell_format['center'])
            worksheet_port.write(s_row - 2, s_col + 13, f"EUR = {rates_today_cb['EUR']}", cell_format['center'])

        def build_market_rates():
            logger.info('printing market rates..')
            worksheet_port.write(s_row - 3, s_col + 9, 'Market', cell_format['bold_center'])
            worksheet_port.write(s_row - 3, s_col + 10, 'last price:', cell_format['bold_center'])
            worksheet_port.write(s_row - 2, s_col + 9, f"USD = {market_rate_today['USD']}", cell_format['center'])
            worksheet_port.write(s_row - 2, s_col + 10, f"EUR = {market_rate_today['EUR']}", cell_format['center'])

        def print_content(pos_type):
            logger.info('content printing: ' + pos_type + 's')
            row = s_row + 1
            col = s_col
            for this_pos in my_positions:
                def print_position_data(row, col):
                    worksheet_port.write(row, col, this_pos.name, cell_format['left'])
                    worksheet_port.write(row, col + 1, this_pos.ticker, cell_format['left'])
                    worksheet_port.write(row, col + 2, this_pos.balance, cell_format['left'])
                    worksheet_port.write(row, col + 3, this_pos.currency, cell_format['left'])

                    if this_pos.currency in supported_currencies:
                        worksheet_port.write(row, col + 4, this_pos.ave_price, cell_format[this_pos.currency])
                        worksheet_port.write(row, col + 5, this_pos.sum_buy, cell_format[this_pos.currency])
                        worksheet_port.write(row, col + 6, this_pos.exp_yield, cell_format[this_pos.currency])
                        worksheet_port.write(row, col + 7, this_pos.market_price, cell_format[this_pos.currency])
                        worksheet_port.write(row, col + 9, this_pos.market_cost, cell_format[this_pos.currency])
                        worksheet_port.write(row, col + 10, this_pos.market_cost * market_rate_today[this_pos.currency],
                                             cell_format['RUB'])
                    else:
                        worksheet_port.write(row, col + 4, 'unknown currency', cell_format['right'])
                        worksheet_port.write(row, col + 5, 'unknown currency', cell_format['right'])
                        worksheet_port.write(row, col + 6, 'unknown currency', cell_format['right'])
                        worksheet_port.write(row, col + 8, 'unknown currency', cell_format['right'])
                        worksheet_port.write(row, col + 9, 'unknown currency', cell_format['right'])
                        worksheet_port.write(row, col + 10, 'unknown currency', cell_format['right'])

                    # % change
                    cell_format['perc'] = workbook.add_format({'num_format': '0.00  ',
                                                               'font_color': get_color(this_pos.percent_change)})
                    worksheet_port.write(row, col + 8, this_pos.percent_change, cell_format['perc'])

                    worksheet_port.write(row, col + 12, this_pos.market_cost_rub_cb, cell_format['RUB'])
                    worksheet_port.write(row, col + 13, this_pos.ave_buy_price_rub, cell_format['RUB'])
                    worksheet_port.write(row, col + 14, this_pos.sum_buy_rub, cell_format['RUB'])
                    worksheet_port.write(row, col + 15, this_pos.tax_base, cell_format['RUB'])
                    worksheet_port.write(row, col + 16, this_pos.exp_tax, cell_format['RUB'])

                    row += 1

                    return row

                if this_pos.position_type == pos_type:
                    row = print_position_data(row, col)

                if pos_type == "Other":
                    if this_pos.position_type != "Stock"\
                            and this_pos.position_type != "Bond"\
                            and this_pos.position_type != "Etf"\
                            and this_pos.position_type != "Currency":
                        row = print_position_data(row, col)

            return row

        def print_totals(row, col):
            worksheet_port.write(row, col, 'Рубль деревянный кэшем', cell_format['left'])
            for shift in [2, 10, 12]:
                worksheet_port.write(row, col + shift, cash_rub, cell_format['RUB'])
            for shift in set(range(1, 17)) - {2, 10, 11, 12}:
                worksheet_port.write(row, col + shift, '-', cell_format['center'])
            row += 1

            # portfolio market cost in rub
            worksheet_port.write(row + 1, col + 9, 'total value:', cell_format['bold_right'])
            worksheet_port.write(row + 1, col + 10, portfolio_cost_rub_market, cell_format['RUB'])
            # average percent
            worksheet_port.write(row + 1, col + 7, 'ave. %', cell_format['bold_right'])

            cell_format['perc'] = workbook.add_format(
                {'num_format': '0.00  ', 'font_color': get_color(average_percent)})
            worksheet_port.write(row + 1, col + 8, average_percent, cell_format['perc'])

            worksheet_port.write(row + 1, col + 12, sum_profile['portfolio_value_rub_cb'], cell_format['RUB'])

            worksheet_port.write(row + 1, col + 14, sum_profile['pos_ave_buy_rub'], cell_format['RUB'])
            worksheet_port.write(row + 2, col + 14, 'profit:', cell_format['bold_right'])
            worksheet_port.write(row + 3, col + 14, 'loss:', cell_format['bold_right'])

            worksheet_port.write(row + 2, col + 15, sum_profile['profit'], cell_format['RUB'])
            worksheet_port.write(row + 3, col + 15, sum_profile['loss'], cell_format['RUB'])

            worksheet_port.write(row + 2, col + 16, sum_profile['profit_tax'], cell_format['RUB'])
            worksheet_port.write(row + 3, col + 16, sum_profile['loss_tax'], cell_format['RUB'])
            worksheet_port.write(row + 4, col + 16, sum_profile['exp_tax'], cell_format['RUB'])

            return row + 1

        # execute
        set_columns_width()
        build_header()
        build_cb_rate()
        build_market_rates()
        s_row = print_content("Stock")
        s_row = print_content("Bond")
        s_row = print_content("Etf")
        s_row = print_content("Other")
        last_row = print_content("Currency")
        print_totals(last_row, s_col)

        return last_row

    def print_operations(s_row, s_col):
        logger.info('building operations table..')
        start_col = 1
        def print_operations_by_type(ops_type, start_row, start_col):
            # set column width
            worksheet_ops.set_column(start_col, start_col, 18, cell_format['right'])
            worksheet_ops.set_column(start_col + 1, start_col + 1, 16, cell_format['right'])
            worksheet_ops.set_column(start_col + 2, start_col + 2, 4, cell_format['right'])

            # header
            name = ops_type + ' operations'
            worksheet_ops.write(start_row, start_col, name, cell_format['bold_center'])
            worksheet_ops.write(start_row, start_col + 1, 'value', cell_format['bold_center'])
            # body
            start_row += 1
            worksheet_ops.write(start_row, start_col, 'start', cell_format['right'])
            for operation in my_operations:
                if operation.op_type == ops_type:
                    # operation's date
                    worksheet_ops.write(start_row, start_col, operation.op_date.strftime('%Y %b %d  %H:%M'), cell_format['left'])
                    # operation's value (payment in the operation's currency)
                    if operation.op_currency in supported_currencies:
                        worksheet_ops.write(start_row, start_col + 1, operation.op_payment, cell_format[operation.op_currency])
                    else:
                        worksheet_ops.write(start_row, start_col + 1, 'unknown currency', cell_format['right'])
                    start_row += 1

            finish_row = start_row + 1
            return finish_row

        def print_operations_with_ticker(ops_type, start_row, start_col):
            # set column width
            worksheet_ops.set_column(start_col, start_col, 18, cell_format['right'])
            worksheet_ops.set_column(start_col + 1, start_col + 1, 16, cell_format['right'])
            worksheet_ops.set_column(start_col + 2, start_col + 2, 16, cell_format['right'])
            worksheet_ops.set_column(start_col + 3, start_col + 3, 4, cell_format['right'])

            # header
            name = ops_type + ' operations'
            worksheet_ops.write(start_row, start_col, name, cell_format['bold_center'])
            worksheet_ops.write(start_row, start_col + 1, 'ticker', cell_format['bold_center'])
            worksheet_ops.write(start_row, start_col + 2, 'value', cell_format['bold_center'])
            # body
            start_row += 1
            worksheet_ops.write(start_row, start_col, 'start', cell_format['right'])
            for operation in my_operations:
                if operation.op_type == ops_type:
                    # operation's date
                    worksheet_ops.write(start_row, start_col, operation.op_date.strftime('%Y %b %d  %H:%M'),
                                        cell_format['left'])
                    # operation's ticker
                    worksheet_ops.write(start_row, start_col + 1, operation.op_ticker,
                                        cell_format['left'])

                    # operation's value (payment in the operation's currency)
                    if operation.op_currency in supported_currencies:
                        worksheet_ops.write(start_row, start_col + 2, operation.op_payment,
                                            cell_format[operation.op_currency])
                    else:
                        worksheet_ops.write(start_row, start_col + 2, 'unknown currency', cell_format['right'])
                    start_row += 1

            finish_row = start_row + 1
            return finish_row

        # PAY IN operations
        logger.info('building Pay In operations list..')
        finish_row_payin = print_operations_by_type('PayIn', s_row, s_col)
        worksheet_ops.write(finish_row_payin, s_col + 1, sum_profile['payin'], cell_format['RUB'])

        # PAY OUT operations
        logger.info('building Pay Out operations list..')
        finish_row_payout = print_operations_by_type('PayOut', s_row, s_col + 3)
        worksheet_ops.write(finish_row_payout, s_col + 4, sum_profile['payout'], cell_format['RUB'])

        # BUY operations
        logger.info('building Buy operations list..')
        last_row_buy = print_operations_with_ticker('Buy', s_row, s_col + 6)
        worksheet_ops.write(last_row_buy, s_col + 8, sum_profile['buy'], cell_format['RUB'])
        # BUY CARD operations
        logger.info('building Buy Card operations list..')
        last_row_buycard = print_operations_with_ticker('BuyCard', last_row_buy + 3, s_col + 6)
        worksheet_ops.write(last_row_buycard, s_col + 8, sum_profile['buycard'], cell_format['RUB'])

        # SELL operations
        logger.info('building Sell operations list..')
        last_row_sell = print_operations_with_ticker('Sell', s_row, s_col + 10)
        worksheet_ops.write(last_row_sell, s_col + 12, sum_profile['sell'], cell_format['RUB'])

        # Coupon operations
        logger.info('building Coupon operations list..')
        last_row_coupon = print_operations_with_ticker('Coupon', s_row, s_col + 14)
        worksheet_ops.write(last_row_coupon, s_col + 16, sum_profile['coupon'], cell_format['RUB'])

        # Dividend operations
        logger.info('building Dividend operations list..')
        last_row_dividend = print_operations_with_ticker('Dividend', s_row, s_col + 18)
        worksheet_ops.write(last_row_dividend, s_col + 20, sum_profile['dividend'], cell_format['RUB'])

        # Tax operations
        logger.info('building Tax operations list..')
        last_row_tax = print_operations_with_ticker('Tax', s_row, s_col + 22)
        worksheet_ops.write(last_row_tax, s_col + 24, sum_profile['tax'], cell_format['RUB'])
        # Tax Coupon operations
        logger.info('building Tax Coupon operations list..')
        last_row_tax_coupon = print_operations_with_ticker('TaxCoupon', last_row_tax + 3, s_col + 22)
        worksheet_ops.write(last_row_tax_coupon, s_col + 24, sum_profile['taxcoupon'], cell_format['RUB'])
        # Tax Dividend operations
        logger.info('building Tax Dividend operations list..')
        last_row_tax_dividend = print_operations_with_ticker('TaxDividend', last_row_tax_coupon + 3, s_col + 22)
        worksheet_ops.write(last_row_tax_dividend, s_col + 24, sum_profile['taxdividend'], cell_format['RUB'])

        # Commission
        logger.info('building Broker Commission operations list..')
        last_row_broker_commission = print_operations_by_type('BrokerCommission', s_row, s_col + 26)
        worksheet_ops.write(last_row_broker_commission, s_col + 27, sum_profile['brokercommission'], cell_format['RUB'])
        logger.info('building Service Commission operations list..')
        last_row_broker_serv_commission = print_operations_by_type('ServiceCommission', last_row_broker_commission + 3, s_col + 26)
        worksheet_ops.write(last_row_broker_serv_commission, s_col + 27, sum_profile['servicecommission'], cell_format['RUB'])

    def print_statistics(s_row, s_col):
        # investing period
        worksheet_port.write(s_row + 1, s_col, 'Investing period', cell_format['bold_right'])
        worksheet_port.write(s_row + 1, s_col + 1, investing_period_str, cell_format['right'])
        # PayIn - PayOut
        worksheet_port.write(s_row + 2, s_col, 'PayIn - PayOut', cell_format['bold_right'])
        worksheet_port.write(s_row + 2, s_col + 1, payin_payout, cell_format['RUB'])
        # Commissions payed
        worksheet_port.write(s_row + 4, s_col, 'Commissions payed', cell_format['bold_right'])
        worksheet_port.write(s_row + 4, s_col + 1, sum_profile['brokercommission'] + sum_profile['servicecommission'], cell_format['RUB'])
        # Taxes payed
        worksheet_port.write(s_row + 5, s_col, 'Taxes payed', cell_format['bold_right'])
        worksheet_port.write(s_row + 5, s_col + 1, sum_profile['tax'] + sum_profile['taxcoupon'] + sum_profile['taxdividend'], cell_format['RUB'])
        # Clean portfolio (market value without exp.taxes)
        clean_portfolio = portfolio_cost_rub_market - sum_profile['exp_tax']
        worksheet_port.write(s_row + 7, s_col, 'Clean portfolio', cell_format['bold_right'])
        worksheet_port.write(s_row + 7, s_col + 1, clean_portfolio, cell_format['RUB'])
        # Profit (clean portfolio - (PayIn - PayOut))
        worksheet_port.write(s_row + 8, s_col, 'Profit', cell_format['bold_right'])
        worksheet_port.write(s_row + 8, s_col + 1, clean_portfolio - payin_payout, cell_format['RUB'])
        # XIRR value (the irregular internal rate of return)
        worksheet_port.write(s_row + 10, s_col, 'XIRR', cell_format['bold_right'])
        worksheet_port.write(s_row + 10, s_col + 1, str(xirr_value) + " %", cell_format['bold_right'])

    def print_dividends_and_coupons():
        logger.info('printing dividends and coupons statistics..')

        # tax included
        worksheet_divs.merge_range(4, 1, 4, 5,
                                   '* - Налог удержан эмитентом. Самостоятельно доплачиваемые 3%'
                                   ' в таблице не учитываются', merge_format['left_small'])
        start_col = 1
        start_row = 6
        years = []
        for operation in my_operations:
            if operation.op_type == 'Coupon' or operation.op_type == 'Dividend':
                if operation.op_date.strftime('%Y') not in years:
                    years.append(operation.op_date.strftime('%Y'))

        operations_in_last_12_months = []  # needed for dividend salary

        for year in years:
            # header 1 - year
            worksheet_divs.merge_range(start_row, start_col, start_row, start_col + 4, year, merge_format['bold_center'])
            # header 2 - labels
            worksheet_divs.set_column(start_col, start_col + 4, 14, cell_format['right'])
            start_row += 1
            worksheet_divs.write(start_row, start_col, 'Ticker', cell_format['bold_center'])
            worksheet_divs.write(start_row, start_col + 1, 'Date', cell_format['bold_center'])
            worksheet_divs.write(start_row, start_col + 2, 'Value', cell_format['bold_center'])
            worksheet_divs.write(start_row, start_col + 3, 'Tax', cell_format['bold_center'])
            worksheet_divs.write(start_row, start_col + 4, 'Value RUB', cell_format['bold_center'])
            start_row += 1

            # content
            operations_per_year = []
            for operation in my_operations:
                if operation.op_type == 'Coupon' or operation.op_type == 'Dividend':
                    if operation.op_date.strftime('%Y') == year:
                        # print ticker
                        worksheet_divs.write(start_row, start_col, operation.op_ticker,cell_format['left'])
                        # print date
                        worksheet_divs.write(start_row, start_col + 1, operation.op_date.strftime('%Y %b %d'), cell_format['center'])
                        # print value
                        if operation.op_currency in supported_currencies:
                            worksheet_divs.write(start_row, start_col + 2, operation.op_payment, cell_format[operation.op_currency])
                        else:
                            worksheet_divs.write(start_row, start_col + 2, 'unknown currency', cell_format['right'])
                        # print tax
                        tax_payment = 0
                        for tax_op in my_operations:
                            if (tax_op.op_type == 'TaxCoupon' or tax_op.op_type == 'TaxDividend'):
                                if tax_op.op_ticker == operation.op_ticker and tax_op.op_date.strftime('%Y %b %d') == \
                                        operation.op_date.strftime('%Y %b %d'):
                                    tax_payment = tax_op.op_payment
                                    worksheet_divs.write(start_row, start_col + 3, tax_payment,
                                                         cell_format[tax_op.op_currency])
                        if tax_payment == 0:
                            worksheet_divs.write(start_row, start_col + 3, '*', cell_format['right'])

                        # print value RUB
                        worksheet_divs.write(start_row, start_col + 4, operation.op_payment_rub - abs(tax_payment),
                                             cell_format['RUB'])

                        operations_per_year.append(operation.op_payment_rub - abs(tax_payment))
                        if operation.op_in_last_12_months == True:
                            operations_in_last_12_months.append(operation.op_payment_rub - abs(tax_payment))
                        start_row += 1
            # print sum
            worksheet_divs.write(start_row + 1, start_col + 4, sum(operations_per_year), cell_format['RUB'])
            start_col += 6
            start_row = 6

        # dividend salary
        start_col = 1
        start_row = 2
        worksheet_divs.merge_range(start_row, start_col, start_row, start_col + 2,
                                   'average monthly salary for the last 12 months:', merge_format['bold_right'])
        worksheet_divs.write(start_row, start_col + 3, round(sum(operations_in_last_12_months) / 12, 2), cell_format['RUB'])

    def print_clarification(s_row, s_col ):
        logger.info('printing clarification..')
        n = 0
        worksheet_port.write(s_row + n, s_col, 'name', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n , s_col + 1, s_row + n , s_col + 16,
                                   ' - название инструмента',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'ticker', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n , s_col + 1, s_row + n, s_col + 16,
                                   ' - тикер инструмента',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'balance', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n , s_col + 1, s_row + n, s_col + 16,
                                   ' - количество бумаг в портфеле',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'currency', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n , s_col + 1, s_row + n, s_col + 16,
                                   ' - валюта',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'ave.price', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n , s_col + 1, s_row + n, s_col + 16,
                                   ' - средняя цена покупки одной бумаги',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'sum.buy', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n , s_col + 1, s_row + n, s_col + 16,
                                   ' - стоимость приобретения. = ave.price * balance',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'exp.yield', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n , s_col + 1, s_row + n, s_col + 16,
                                   ' - ожидаемый доход при полном закрытии позиции',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'market price', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n , s_col + 1, s_row + n, s_col + 16,
                                   ' - рыночная цена одной бумаги. Берётся из API,'
                                   ' но для облигаций = market value / balance',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, '% change', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n , s_col + 1, s_row + n, s_col + 16,
                                   ' - изменение рыночной стоимости одной бумаги относительно её ave.price',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'market value', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n , s_col + 1, s_row + n, s_col + 16,
                                   ' - рыночная стоимость всей позиции в портфеле',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'market value RUB', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n , s_col + 1, s_row + n, s_col + 16,
                                   ' - market value в рублях по рыночному курсу',
                                   merge_format['left'])
        n += 2
        worksheet_port.write(s_row + n, s_col, 'CB value RUB', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' - тоже market value в рублях, но по курсу ЦБ на сегодня',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'ave.buy in RUB', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' - средняя цена покупки в рублях по курсу ЦБ на день покупки. Рассчитывается сложно',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'sum.buy in RUB', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' - сумма покупки всей позиции в рублях по курсу ЦБ. = ave.buy in RUB * balance',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'tax base', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' - налоговая база. Разница между текущей рыночной стоимостью позиции '
                                   'в рублях по курсу ЦБ и стоимостью её приобретения.'
                                   '= CB value RUB - sum.buy in RUB',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'expected tax', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' - ожидаемый налог. = tax.base * 13%. Не учитывает налоговые льготы и'
                                   'налог, который мог уже набежать по ранее закрытым позициям',
                                   merge_format['left'])
        n += 2
        worksheet_port.write(s_row + n, s_col, 'Investing period', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' - период инвестирования. Сколько лет, месяцев, дней с даты,'
                                   'которая указана в my_account.txt до сегодняшнего дня',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'PayIn - PayOut', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' - разница между заведёнными на счёт средствами и выведенными. ',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'Commissions payed', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' - сумма всех уплаченных комиссий (За торговлю и за обслуживаение)',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'Taxes payed', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' - сумма всех уплаченных налогов (Закрытие позиций, купоны и дивиденды)',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'Clean portfolio', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' - стоимость портфеля, очищенная от налога, '
                                   'начисляемого при закрытии всех позиций. '
                                   'Не учитывает возможные льготы и те налоги,'
                                   ' которые уже могли набежать по ранее закрытым позициям, '
                                   'а также самостоятельно декларируемые налоги',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'Profit', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' - почти чистая прибыль. = Clean portfolio - (PayIn - PayOut)',
                                   merge_format['left'])
        n += 1
        worksheet_port.write(s_row + n, s_col, 'XIRR', cell_format['bold_right'])
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' - the irregular internal rate of return. Показатель на основе формулы Excel, '
                                   'которая рассчитывает эффективность инвестирования '
                                   'с учётом всех пополнений и выводов средств',
                                   merge_format['left'])
        n += 4
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' Разработанно @softandiron и контрибьюторами. Версия v2.x, 2021 год.',
                                   merge_format['left'])
        n += 1
        worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                   ' GitHub: https://github.com/softandiron/tinkproject',
                                   merge_format['left'])
        n += 1

    last_row_pos = print_portfolio(1, 1)
    print_operations(1, 2)
    print_statistics(last_row_pos + 3, 1)
    print_clarification(last_row_pos + 18, 1)
    print_dividends_and_coupons()

    # finish Excel
    logger.info('Excel file composed! With name: '+excel_file_name)
    workbook.close()
