# Creating and filling an Excel file

import xlsxwriter
import data_parser


def build_excel_file(my_positions, my_operations, rates_today_cb, market_rate_today_usd, market_rate_today_eur,
                     average_percent, portfolio_cost_rub_market, sum_portfolio_value_rub_cb, sum_pos_ave_buy_rub,
                     sum_exp_tax,
                     sum_payin, sum_payout, sum_buy, sum_buycard, sum_sell, sum_coupon, sum_dividend,
                     sum_tax, sum_taxcoupon, sum_taxdividend, sum_brokercomission, sum_servicecomission,
                     investing_period_str, cash_rub, payin_payout):
    print(' ')
    print('creating excel file..')
    # creating file
    excel_file_name = 'tinkoffReport_' + data_parser.account_data['now_date'].strftime('%Y.%b.%d') + '.xlsx'
    workbook = xlsxwriter.Workbook(excel_file_name)
    worksheet = workbook.add_worksheet()

    # styles
    cell_format_center = workbook.add_format({'align': 'center'})
    cell_format_right = workbook.add_format({'align': 'right'})
    cell_format_left = workbook.add_format({'align': 'left'})
    cell_format_bold_center = workbook.add_format({'align': 'center', 'bold': True})
    cell_format_bold_right = workbook.add_format({'align': 'right', 'bold': True})
    cell_format_usd = workbook.add_format({'num_format': '## ### ##0.00   [$$-409]', 'align': 'right'})
    cell_format_rub = workbook.add_format({'num_format': '## ### ##0.00   [$₽-ru-RU]', 'align': 'right'})
    cell_format_eur = workbook.add_format({'num_format': '## ### ##0.00   [$€-x-euro1]', 'align': 'right'})
    # cell_format_perc = workbook.add_format({'num_format': '0.00  ', 'font_color': 'black', 'align': 'right'})

    worksheet.set_column('A:A', 16)
    worksheet.write(0, 0, data_parser.account_data['now_date'].strftime('%Y %b %d  %H:%M'), cell_format_bold_center)

    def print_portfolio(s_row, s_col):
        print('building portfolio table..')
        s_row += 3

        def set_columns_width():
            print('setting column width..')
            worksheet.set_column(s_col, s_col, 28)
            worksheet.set_column(s_col + 1, s_col + 1, 14)
            worksheet.set_column(s_col + 2, s_col + 2, 12)
            worksheet.set_column(s_col + 3, s_col + 3, 8)
            worksheet.set_column(s_col + 4, s_col + 4, 12)
            worksheet.set_column(s_col + 5, s_col + 5, 12)
            worksheet.set_column(s_col + 6, s_col + 6, 12)
            worksheet.set_column(s_col + 7, s_col + 7, 10)
            worksheet.set_column(s_col + 8, s_col + 8, 14)
            worksheet.set_column(s_col + 9, s_col + 9, 16)

            worksheet.set_column(s_col + 11, s_col + 16, 16)

        def build_header():
            print('printing header..')
            worksheet.write(s_row, s_col, 'name', cell_format_bold_center)
            worksheet.write(s_row, s_col + 1, 'ticker', cell_format_bold_center)
            worksheet.write(s_row, s_col + 2, 'balance', cell_format_bold_center)
            worksheet.write(s_row, s_col + 3, 'currency', cell_format_bold_center)
            worksheet.write(s_row, s_col + 4, 'ave.price', cell_format_bold_center)
            worksheet.write(s_row, s_col + 5, 'exp.yield', cell_format_bold_center)
            worksheet.write(s_row, s_col + 6, 'market price', cell_format_bold_center)
            worksheet.write(s_row, s_col + 7, '% change', cell_format_bold_center)
            worksheet.write(s_row, s_col + 8, 'market value', cell_format_bold_center)
            worksheet.write(s_row, s_col + 9, 'market value RUB', cell_format_bold_center)

            worksheet.write(s_row, s_col + 11, 'CB value RUB', cell_format_bold_center)
            worksheet.write(s_row, s_col + 12, 'ave.buy in RUB', cell_format_bold_center)
            worksheet.write(s_row, s_col + 13, 'sum.buy in RUB', cell_format_bold_center)
            worksheet.write(s_row, s_col + 14, 'tax base', cell_format_bold_center)
            worksheet.write(s_row, s_col + 15, 'expected tax', cell_format_bold_center)

        def build_cb_rate():
            print('printing CB rates..')
            worksheet.write(s_row - 3, s_col + 11, 'Central Bank', cell_format_bold_center)
            worksheet.write(s_row - 3, s_col + 12, 'today rates:', cell_format_bold_center)
            worksheet.write(s_row - 2, s_col + 11, 'USD = ' + str(rates_today_cb['USD'].value), cell_format_center)
            worksheet.write(s_row - 2, s_col + 12, 'EUR = ' + str(rates_today_cb['EUR'].value), cell_format_center)

        def build_market_rates():
            print('printing market rates..')
            worksheet.write(s_row - 3, s_col + 8, 'Market', cell_format_bold_center)
            worksheet.write(s_row - 3, s_col + 9, 'today rates:', cell_format_bold_center)
            worksheet.write(s_row - 2, s_col + 8, 'USD = ' + str(market_rate_today_usd), cell_format_center)
            worksheet.write(s_row - 2, s_col + 9, 'EUR = ' + str(market_rate_today_eur), cell_format_center)

        def print_content():
            print('content printing..')
            row = s_row + 1
            col = s_col
            for this_pos in my_positions:
                # name
                worksheet.write(row, col, this_pos.name, cell_format_left)
                # ticker
                worksheet.write(row, col + 1, this_pos.ticker, cell_format_left)
                # balance
                worksheet.write(row, col + 2, this_pos.balance, cell_format_left)
                # currency
                worksheet.write(row, col + 3, this_pos.currency, cell_format_left)
                # ave.price
                if this_pos.currency == 'RUB':
                    worksheet.write(row, col + 4, this_pos.ave_price, cell_format_rub)
                elif this_pos.currency == 'USD':
                    worksheet.write(row, col + 4, this_pos.ave_price, cell_format_usd)
                elif this_pos.currency == 'EUR':
                    worksheet.write(row, col + 4, this_pos.ave_price, cell_format_eur)
                else:
                    worksheet.write(row, col + 4, 'unknown currency', cell_format_right)
                # exp.yield
                if this_pos.currency == 'RUB':
                    worksheet.write(row, col + 5, this_pos.exp_yield, cell_format_rub)
                elif this_pos.currency == 'USD':
                    worksheet.write(row, col + 5, this_pos.exp_yield, cell_format_usd)
                elif this_pos.currency == 'EUR':
                    worksheet.write(row, col + 5, this_pos.exp_yield, cell_format_eur)
                else:
                    worksheet.write(row, col + 5, 'unknown currency', cell_format_right)
                # market price
                if this_pos.currency == 'RUB':
                    worksheet.write(row, col + 6, this_pos.market_price, cell_format_rub)
                elif this_pos.currency == 'USD':
                    worksheet.write(row, col + 6, this_pos.market_price, cell_format_usd)
                elif this_pos.currency == 'EUR':
                    worksheet.write(row, col + 6, this_pos.market_price, cell_format_eur)
                else:
                    worksheet.write(row, col + 6, 'unknown currency', cell_format_right)
                # % change
                if this_pos.percent_change > 0:
                    cell_format_perc = workbook.add_format({'num_format': '0.00  ', 'font_color': 'green'})
                elif this_pos.percent_change < 0:
                    cell_format_perc = workbook.add_format({'num_format': '0.00  ', 'font_color': 'red'})
                else:
                    cell_format_perc = workbook.add_format({'num_format': '0.00  ', 'font_color': 'black'})
                worksheet.write(row, col + 7, this_pos.percent_change, cell_format_perc)
                # market value
                if this_pos.currency == 'RUB':
                    worksheet.write(row, col + 8, this_pos.market_cost, cell_format_rub)
                elif this_pos.currency == 'USD':
                    worksheet.write(row, col + 8, this_pos.market_cost, cell_format_usd)
                elif this_pos.currency == 'EUR':
                    worksheet.write(row, col + 8, this_pos.market_cost, cell_format_eur)
                else:
                    worksheet.write(row, col + 8, 'unknown currency', cell_format_right)
                # market value rub
                if this_pos.currency == 'RUB':
                    market_cost_rub = this_pos.market_cost
                    worksheet.write(row, col + 9, market_cost_rub, cell_format_rub)
                elif this_pos.currency == 'USD':
                    market_cost_rub = this_pos.market_cost * market_rate_today_usd
                    worksheet.write(row, col + 9, market_cost_rub, cell_format_rub)
                elif this_pos.currency == 'EUR':
                    market_cost_rub = this_pos.market_cost * market_rate_today_eur
                    worksheet.write(row, col + 9, market_cost_rub, cell_format_rub)
                else:
                    worksheet.write(row, col + 8, 'unknown currency', cell_format_right)

                # market value rub CB
                worksheet.write(row, col + 11, this_pos.market_cost_rub_cb, cell_format_rub)
                # average buy price in rub
                worksheet.write(row, col + 12, this_pos.ave_buy_price_rub, cell_format_rub)
                # sum buy in rub
                worksheet.write(row, col + 13, this_pos.sum_buy_rub, cell_format_rub)
                # tax base
                worksheet.write(row, col + 14, this_pos.tax_base, cell_format_rub)
                # expected tax
                worksheet.write(row, col + 15, this_pos.exp_tax, cell_format_rub)

                row += 1

            # portfolio RUB cash
            worksheet.write(row, col, 'Рубль деревянный кэшем', cell_format_left)
            worksheet.write(row, col + 1, '-', cell_format_center)
            worksheet.write(row, col + 2, cash_rub, cell_format_rub)
            worksheet.write(row, col + 3, '-', cell_format_center)
            worksheet.write(row, col + 4, '-', cell_format_center)
            worksheet.write(row, col + 5, '-', cell_format_center)
            worksheet.write(row, col + 6, '-', cell_format_center)
            worksheet.write(row, col + 7, '-', cell_format_center)
            worksheet.write(row, col + 8, '-', cell_format_center)
            worksheet.write(row, col + 9, cash_rub, cell_format_rub)

            worksheet.write(row, col + 11, cash_rub, cell_format_rub)
            worksheet.write(row, col + 12, '-', cell_format_center)
            worksheet.write(row, col + 13, '-', cell_format_center)
            worksheet.write(row, col + 14, '-', cell_format_center)
            worksheet.write(row, col + 15, '-', cell_format_center)
            row += 1

            # portfolio market cost in rub
            worksheet.write(row + 1, col + 8, 'total value:', cell_format_bold_right)
            worksheet.write(row + 1, col + 9, portfolio_cost_rub_market, cell_format_rub)
            # average percent
            worksheet.write(row + 1, col + 6, 'ave. %', cell_format_bold_right)
            if average_percent > 0:
                cell_format_perc = workbook.add_format({'num_format': '0.00  ', 'font_color': 'green'})
            elif average_percent < 0:
                cell_format_perc = workbook.add_format({'num_format': '0.00  ', 'font_color': 'red'})
            else:
                cell_format_perc = workbook.add_format({'num_format': '0.00  ', 'font_color': 'black'})
            worksheet.write(row + 1, col + 7, average_percent, cell_format_perc)
            # cell_format_perc = workbook.add_format({'num_format': '0.00  ', 'font_color': 'black'})

            # sum CB value RUB
            worksheet.write(row + 1, col + 11, sum_portfolio_value_rub_cb, cell_format_rub)

            # sum of average buy price in rub
            worksheet.write(row + 1, col + 13, sum_pos_ave_buy_rub, cell_format_rub)

            # sum of expected taxes
            worksheet.write(row + 1, col + 15, sum_exp_tax, cell_format_rub)

            return row

        # execute
        set_columns_width()
        build_header()
        build_cb_rate()
        build_market_rates()
        last_row = print_content()

        return last_row

    def print_operations(s_row, s_col):
        print('building operations table..')

        def print_operations_by_type(ops_type, start_row, start_col):
            # set column width
            worksheet.set_column(start_col, start_col, 17, cell_format_right)
            worksheet.set_column(start_col + 1, start_col + 1, 16, cell_format_right)
            worksheet.set_column(start_col + 2, start_col + 2, 4, cell_format_right)

            # header
            name = ops_type + ' operations'
            worksheet.write(start_row, start_col, name, cell_format_bold_center)
            worksheet.write(start_row, start_col + 1, 'value', cell_format_bold_center)
            # body
            start_row += 1
            worksheet.write(start_row, start_col, 'start', cell_format_right)
            for operation in my_operations:
                if operation.op_type == ops_type:
                    # operation's date
                    worksheet.write(start_row, start_col, operation.op_date.strftime('%Y %b %d  %H:%M'),
                                    cell_format_right)
                    # operation's value (payment in the operation's currency)
                    if operation.op_currency == 'RUB':
                        worksheet.write(start_row, start_col + 1, operation.op_payment, cell_format_rub)
                    elif operation.op_currency == 'USD':
                        worksheet.write(start_row, start_col + 1, operation.op_payment, cell_format_usd)
                    elif operation.op_currency == 'EUR':
                        worksheet.write(start_row, start_col + 1, operation.op_payment, cell_format_eur)
                    else:
                        worksheet.write(start_row, start_col + 1, 'unknown currency', cell_format_right)
                    start_row += 1

            finish_row = start_row + 1
            return finish_row

        # PAY IN operations
        print('building Pay In operations list..')
        finish_row_payin = print_operations_by_type('PayIn', s_row, s_col)
        worksheet.write(finish_row_payin, s_col + 1, sum_payin, cell_format_rub)

        # PAY OUT operations
        print('building Pay Out operations list..')
        finish_row_payout = print_operations_by_type('PayOut', s_row, s_col + 3)
        worksheet.write(finish_row_payout, s_col + 4, sum_payout, cell_format_rub)

        # BUY operations
        print('building Buy operations list..')
        last_row_buy = print_operations_by_type('Buy', s_row, s_col + 6)
        worksheet.write(last_row_buy, s_col + 7, sum_buy, cell_format_rub)
        # BUY CARD operations
        print('building Buy Card operations list..')
        last_row_buycard = print_operations_by_type('BuyCard', last_row_buy + 3, s_col + 6)
        worksheet.write(last_row_buycard, s_col + 7, sum_buycard, cell_format_rub)

        # SELL operations
        print('building Sell operations list..')
        last_row_sell = print_operations_by_type('Sell', s_row, s_col + 9)
        worksheet.write(last_row_sell, s_col + 10, sum_sell, cell_format_rub)

        # Coupon operations
        print('building Coupon operations list..')
        last_row_coupon = print_operations_by_type('Coupon', s_row, s_col + 12)
        worksheet.write(last_row_coupon, s_col + 13, sum_coupon, cell_format_rub)

        # Dividend operations
        print('building Dividend operations list..')
        last_row_dividend = print_operations_by_type('Dividend', s_row, s_col + 15)
        worksheet.write(last_row_dividend, s_col + 16, sum_dividend, cell_format_rub)

        # Tax operations
        print('building Tax operations list..')
        last_row_tax = print_operations_by_type('Tax', s_row, s_col + 18)
        worksheet.write(last_row_tax, s_col + 19, sum_tax, cell_format_rub)
        # Tax Coupon operations
        print('building Tax Coupon operations list..')
        last_row_tax_coupon = print_operations_by_type('TaxCoupon', last_row_tax + 3, s_col + 18)
        worksheet.write(last_row_tax_coupon, s_col + 19, sum_taxcoupon, cell_format_rub)
        # Tax Dividend operations
        print('building Tax Dividend operations list..')
        last_row_tax_dividend = print_operations_by_type('TaxDividend', last_row_tax_coupon + 3, s_col + 18)
        worksheet.write(last_row_tax_dividend, s_col + 19, sum_taxdividend, cell_format_rub)

        # Commission
        print('building Broker Commission operations list..')
        last_row_broker_commission = print_operations_by_type('BrokerCommission', s_row, s_col + 21)
        worksheet.write(last_row_broker_commission, s_col + 22, sum_brokercomission, cell_format_rub)
        print('building Service Commission operations list..')
        last_row_broker_serv_commission = print_operations_by_type('ServiceCommission', last_row_broker_commission + 3,
                                                                                         s_col + 21)
        worksheet.write(last_row_broker_serv_commission, s_col + 22, sum_servicecomission, cell_format_rub)

    def print_statistics(s_row, s_col):
        # investing period
        worksheet.write(s_row + 1, s_col, 'Investing period', cell_format_bold_right)
        worksheet.write(s_row + 1, s_col + 1, investing_period_str, cell_format_right)
        # PayIn - PayOut
        worksheet.write(s_row + 2, s_col, 'PayIn - PayOut', cell_format_bold_right)
        worksheet.write(s_row + 2, s_col + 1, payin_payout, cell_format_rub)
        # Commissions payed
        worksheet.write(s_row + 4, s_col, 'Commissions payed', cell_format_bold_right)
        worksheet.write(s_row + 4, s_col + 1, sum_brokercomission + sum_servicecomission, cell_format_rub)
        # Taxes payed
        worksheet.write(s_row + 5, s_col, 'Taxes payed', cell_format_bold_right)
        worksheet.write(s_row + 5, s_col + 1, sum_tax + sum_taxcoupon + sum_taxdividend, cell_format_rub)
        # Clean portfolio (market value without exp.taxes)
        clean_portfolio = portfolio_cost_rub_market - sum_exp_tax
        worksheet.write(s_row + 7, s_col, 'Clean portfolio', cell_format_bold_right)
        worksheet.write(s_row + 7, s_col + 1, clean_portfolio, cell_format_rub)
        # Profit (clean portfolio - (PayIn - PayOut))
        worksheet.write(s_row + 8, s_col, 'Profit', cell_format_bold_right)
        worksheet.write(s_row + 8, s_col + 1, clean_portfolio - payin_payout, cell_format_rub)

    last_row_pos = print_portfolio(1, 1)
    print_operations(1, 18)
    print_statistics(last_row_pos + 3, 1)

    # finish Excel
    print(' ')
    print('Excel file composed! With name:')
    print(excel_file_name)
    workbook.close()
