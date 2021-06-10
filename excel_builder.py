# Creating and filling an Excel file

import logging
import xlsxwriter
import data_parser


def get_color(num):
    if num > 0:
        return 'green'
    if num < 0:
        return 'red'
    return 'black'


def build_excel_file(my_positions, my_operations, rates_today_cb, market_rate_today,
                     average_percent, portfolio_cost_rub_market, sum_profile,
                     investing_period_str, cash_rub, payin_payout, logger=logging.getLogger()):

    logger.info('creating excel file..')
    excel_file_name = 'tinkoffReport_' + data_parser.account_data['now_date'].strftime('%Y.%b.%d') + '.xlsx'
    workbook = xlsxwriter.Workbook(excel_file_name)
    worksheet_port = workbook.add_worksheet("Portfolio")
    worksheet_ops = workbook.add_worksheet("Operations")

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

    worksheet_port.set_column('A:A', 16)
    worksheet_port.write(0, 0, data_parser.account_data['now_date'].strftime('%Y %b %d  %H:%M'), cell_format['bold_center'])

    def print_portfolio(s_row, s_col):
        logger.info('building portfolio table..')
        s_row += 3

        def set_columns_width():
            logger.info('setting column width..')
            worksheet_port.set_column(s_col, s_col, 28)
            worksheet_port.set_column(s_col + 1, s_col + 1, 14)
            worksheet_port.set_column(s_col + 2, s_col + 2, 12)
            worksheet_port.set_column(s_col + 3, s_col + 3, 8)
            worksheet_port.set_column(s_col + 4, s_col + 4, 12)
            worksheet_port.set_column(s_col + 5, s_col + 5, 12)
            worksheet_port.set_column(s_col + 6, s_col + 6, 12)
            worksheet_port.set_column(s_col + 7, s_col + 7, 10)
            worksheet_port.set_column(s_col + 8, s_col + 8, 14)
            worksheet_port.set_column(s_col + 9, s_col + 9, 16)

            worksheet_port.set_column(s_col + 11, s_col + 16, 16)

        def build_header():
            logger.info('printing header..')

            for shift, name in enumerate(['name', 'ticker', 'balance', 'currency', 'ave.price', 'exp.yield', 'market price', '% change', 'market value', 'market value RUB', '', 'CB value RUB', 'ave.buy in RUB', 'sum.buy in RUB', 'tax base', 'expected tax']):
                worksheet_port.write(s_row, s_col+shift, name, cell_format['bold_center'])

        def build_cb_rate():
            logger.info('printing CB rates..')
            worksheet_port.write(s_row - 3, s_col + 11, 'Central Bank', cell_format['bold_center'])
            worksheet_port.write(s_row - 3, s_col + 12, 'today rates:', cell_format['bold_center'])
            worksheet_port.write(s_row - 2, s_col + 11, f"USD = {rates_today_cb['USD'].value}", cell_format['center'])
            worksheet_port.write(s_row - 2, s_col + 12, f"EUR = {rates_today_cb['EUR'].value}", cell_format['center'])

        def build_market_rates():
            logger.info('printing market rates..')
            worksheet_port.write(s_row - 3, s_col + 8, 'Market', cell_format['bold_center'])
            worksheet_port.write(s_row - 3, s_col + 9, 'today rates:', cell_format['bold_center'])
            worksheet_port.write(s_row - 2, s_col + 8, f"USD = {market_rate_today['USD']}", cell_format['center'])
            worksheet_port.write(s_row - 2, s_col + 9, f"EUR = {market_rate_today['EUR']}", cell_format['center'])

        def print_content():
            logger.info('content printing..')
            row = s_row + 1
            col = s_col
            for this_pos in my_positions:
                worksheet_port.write(row, col, this_pos.name, cell_format['left'])
                worksheet_port.write(row, col + 1, this_pos.ticker, cell_format['left'])
                worksheet_port.write(row, col + 2, this_pos.balance, cell_format['left'])
                worksheet_port.write(row, col + 3, this_pos.currency, cell_format['left'])

                if this_pos.currency in ['RUB', 'USD', 'EUR']:
                    worksheet_port.write(row, col + 4, this_pos.ave_price, cell_format[this_pos.currency])
                    worksheet_port.write(row, col + 5, this_pos.exp_yield, cell_format[this_pos.currency])
                    worksheet_port.write(row, col + 6, this_pos.market_price, cell_format[this_pos.currency])
                    worksheet_port.write(row, col + 8, this_pos.market_cost, cell_format[this_pos.currency])
                    worksheet_port.write(row, col + 9, this_pos.market_cost * market_rate_today[this_pos.currency], cell_format['RUB'])
                else:
                    worksheet_port.write(row, col + 4, 'unknown currency', cell_format['right'])
                    worksheet_port.write(row, col + 5, 'unknown currency', cell_format['right'])
                    worksheet_port.write(row, col + 6, 'unknown currency', cell_format['right'])
                    worksheet_port.write(row, col + 8, 'unknown currency', cell_format['right'])
                    worksheet_port.write(row, col + 9, 'unknown currency', cell_format['right'])

                # % change
                cell_format['perc'] = workbook.add_format({'num_format': '0.00  ', 'font_color': get_color(this_pos.percent_change)})
                worksheet_port.write(row, col + 7, this_pos.percent_change, cell_format['perc'])

                worksheet_port.write(row, col + 11, this_pos.market_cost_rub_cb, cell_format['RUB'])
                worksheet_port.write(row, col + 12, this_pos.ave_buy_price_rub, cell_format['RUB'])
                worksheet_port.write(row, col + 13, this_pos.sum_buy_rub, cell_format['RUB'])
                worksheet_port.write(row, col + 14, this_pos.tax_base, cell_format['RUB'])
                worksheet_port.write(row, col + 15, this_pos.exp_tax, cell_format['RUB'])

                row += 1

            worksheet_port.write(row, col, 'Рубль деревянный кэшем', cell_format['left'])
            for shift in [2, 9, 11]:
                worksheet_port.write(row, col+shift, cash_rub, cell_format['RUB'])
            for shift in set(range(1, 16)) - {2, 9, 10, 11}:
                worksheet_port.write(row, col+shift, '-', cell_format['center'])
            row += 1

            # portfolio market cost in rub
            worksheet_port.write(row + 1, col + 8, 'total value:', cell_format['bold_right'])
            worksheet_port.write(row + 1, col + 9, portfolio_cost_rub_market, cell_format['RUB'])
            # average percent
            worksheet_port.write(row + 1, col + 6, 'ave. %', cell_format['bold_right'])

            cell_format['perc'] = workbook.add_format({'num_format': '0.00  ', 'font_color': get_color(average_percent)})
            worksheet_port.write(row + 1, col + 7, average_percent, cell_format['perc'])

            worksheet_port.write(row + 1, col + 11, sum_profile['portfolio_value_rub_cb'], cell_format['RUB'])
            worksheet_port.write(row + 1, col + 13, sum_profile['pos_ave_buy_rub'], cell_format['RUB'])
            worksheet_port.write(row + 1, col + 15, sum_profile['exp_tax'], cell_format['RUB'])

            return row

        # execute
        set_columns_width()
        build_header()
        build_cb_rate()
        build_market_rates()
        last_row = print_content()

        return last_row

    def print_operations(s_row, s_col):
        logger.info('building operations table..')
        start_col = 1
        def print_operations_by_type(ops_type, start_row, start_col):
            # set column width
            worksheet_ops.set_column(start_col, start_col, 17, cell_format['right'])
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
                    worksheet_ops.write(start_row, start_col, operation.op_date.strftime('%Y %b %d  %H:%M'), cell_format['right'])
                    # operation's value (payment in the operation's currency)
                    if operation.op_currency in ['RUB', 'USD', 'EUR']:
                        worksheet_ops.write(start_row, start_col + 1, operation.op_payment, cell_format[operation.op_currency])
                    else:
                        worksheet_ops.write(start_row, start_col + 1, 'unknown currency', cell_format['right'])
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
        last_row_buy = print_operations_by_type('Buy', s_row, s_col + 6)
        worksheet_ops.write(last_row_buy, s_col + 7, sum_profile['buy'], cell_format['RUB'])
        # BUY CARD operations
        logger.info('building Buy Card operations list..')
        last_row_buycard = print_operations_by_type('BuyCard', last_row_buy + 3, s_col + 6)
        worksheet_ops.write(last_row_buycard, s_col + 7, sum_profile['buycard'], cell_format['RUB'])

        # SELL operations
        logger.info('building Sell operations list..')
        last_row_sell = print_operations_by_type('Sell', s_row, s_col + 9)
        worksheet_ops.write(last_row_sell, s_col + 10, sum_profile['sell'], cell_format['RUB'])

        # Coupon operations
        logger.info('building Coupon operations list..')
        last_row_coupon = print_operations_by_type('Coupon', s_row, s_col + 12)
        worksheet_ops.write(last_row_coupon, s_col + 13, sum_profile['coupon'], cell_format['RUB'])

        # Dividend operations
        logger.info('building Dividend operations list..')
        last_row_dividend = print_operations_by_type('Dividend', s_row, s_col + 15)
        worksheet_ops.write(last_row_dividend, s_col + 16, sum_profile['dividend'], cell_format['RUB'])

        # Tax operations
        logger.info('building Tax operations list..')
        last_row_tax = print_operations_by_type('Tax', s_row, s_col + 18)
        worksheet_ops.write(last_row_tax, s_col + 19, sum_profile['tax'], cell_format['RUB'])
        # Tax Coupon operations
        logger.info('building Tax Coupon operations list..')
        last_row_tax_coupon = print_operations_by_type('TaxCoupon', last_row_tax + 3, s_col + 18)
        worksheet_ops.write(last_row_tax_coupon, s_col + 19, sum_profile['taxcoupon'], cell_format['RUB'])
        # Tax Dividend operations
        logger.info('building Tax Dividend operations list..')
        last_row_tax_dividend = print_operations_by_type('TaxDividend', last_row_tax_coupon + 3, s_col + 18)
        worksheet_ops.write(last_row_tax_dividend, s_col + 19, sum_profile['taxdividend'], cell_format['RUB'])

        # Commission
        logger.info('building Broker Commission operations list..')
        last_row_broker_commission = print_operations_by_type('BrokerCommission', s_row, s_col + 21)
        worksheet_ops.write(last_row_broker_commission, s_col + 22, sum_profile['brokercommission'], cell_format['RUB'])
        logger.info('building Service Commission operations list..')
        last_row_broker_serv_commission = print_operations_by_type('ServiceCommission', last_row_broker_commission + 3, s_col + 21)
        worksheet_ops.write(last_row_broker_serv_commission, s_col + 22, sum_profile['servicecommission'], cell_format['RUB'])

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

    last_row_pos = print_portfolio(1, 1)
    print_operations(1, 2)
    print_statistics(last_row_pos + 3, 1)

    # finish Excel
    logger.info('Excel file composed! With name: '+excel_file_name)
    workbook.close()
