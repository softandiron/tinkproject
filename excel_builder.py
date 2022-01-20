# Creating and filling an Excel file

import logging
import xlsxwriter
import data_parser

import currencies

from configuration import Config

# For backward compatibility - needs to be deprecated later
# after merging parts tables
supported_currencies = currencies.supported_currencies
assets_types = ['share', 'bond', 'etf', 'futures', 'currency']

logger = logging.getLogger("ExBuild")
logger.setLevel(logging.INFO)


def get_color(num):
    if num > 0:
        return 'green'
    if num < 0:
        return 'red'
    return 'black'


def build_excel_file(account, my_positions, my_operations, rates_today_cb, market_rate_today,
                     average_percent, portfolio_cost_rub_market, sum_profile,
                     investing_period_str, cash_rub, payin_payout, xirr_value, tax_rate):

    logger.info('creating excel file..')
    excel_file_name = config.get_account_filename(account.broker_account_id)
    excel_file_name = str(excel_file_name) + '.xlsx'
    workbook = xlsxwriter.Workbook(excel_file_name)
    workbook.set_size(1440, 1024)  # set default window size
    worksheet_port = workbook.add_worksheet("Portfolio")
    worksheet_oplist = workbook.add_worksheet("Operations list")
    worksheet_divs = workbook.add_worksheet("Coupons and Dividends")
    worksheet_deduct = workbook.add_worksheet("IIS Deduction")
    worksheet_parts = workbook.add_worksheet("Parts")

    # styles
    cell_format = {}
    cell_format['center'] = workbook.add_format({'align': 'center'})
    cell_format['right'] = workbook.add_format({'align': 'right'})
    cell_format['right_number'] = workbook.add_format({'align': 'right',
                                                       'num_format': '## ### ##0.00'})
    cell_format['left'] = workbook.add_format({'align': 'left'})
    cell_format['bold_center'] = workbook.add_format({'align': 'center', 'bold': True})
    cell_format['bold_right'] = workbook.add_format({'align': 'right', 'bold': True})
    cell_format['date_time'] = workbook.add_format({'align': 'center',
                                                    'num_format': 'YYYY-MM-DD hh:mm:ss;@'})
    for currency, data in currencies.currencies_data.items():
        cell_format[currency] = workbook.add_format({'num_format': data['num_format'],
                                                     'align': 'right'})
        cell_format[f'{currency}-bold'] = workbook.add_format({'num_format': data['num_format'],
                                                               'align': 'right', 'bold': True})
        cell_format[f'{currency}-bold-total'] = workbook.add_format({'num_format': data['num_format'],
                                                                     'align': 'right', 'bold': True})
        cell_format[f'{currency}-bold-total'].set_top(1)
    merge_format = {}
    merge_format['bold_center'] = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True})
    merge_format['bold_right'] = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bold': True})
    merge_format['bold_left'] = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': True})
    merge_format['left'] = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': False})
    merge_format['left_small'] = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bold': False, 'font_size': '9'})

    worksheet_port.set_column('A:A', 16)
    worksheet_port.write(0, 0, config.now_date.strftime('%Y %b %d  %H:%M'), cell_format['bold_center'])

    def print_headers(worksheet, start_col, start_row, headers=[], set_filter=True):
        """Вывод строки заголовков и установка нужной ширины столбца

        Args:
            worksheet: лист, на котором надо сделать
            start_col (int): начальная колонка
            start_row (int): начальный ряд
            headers (list, optional): список рядов в формате [["название столбца", ширина], ...].
                                      Defaults to [].
            set_filter (bool, optional): Формировать ли фильрацию списка. Defaults to True.
        """
        n = 0
        for header in headers:
            worksheet.write(start_row, start_col + n, header[0], cell_format['bold_center'])
            worksheet.set_column(start_col+n, start_col+n, header[1])
            n += 1
        if set_filter:
            worksheet.autofilter(start_row, start_col, start_row, start_col+n-1)

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
                    if this_pos.position_type != "currency":
                        worksheet_port.write(row, col + 2, this_pos.balance, cell_format['right'])
                        worksheet_port.write(row, col + 3, this_pos.currency, cell_format['left'])
                    else:
                        worksheet_port.write(row, col + 2, this_pos.balance, cell_format['right_number'])
                        # для валютных позиций вывести их 3-буквенное обозначение
                        code = currencies.currency_code_by_figi(this_pos.figi)
                        worksheet_port.write(row, col + 3, code, cell_format['left'])

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
                    if this_pos.position_type != "share"\
                            and this_pos.position_type != "bond"\
                            and this_pos.position_type != "etf"\
                            and this_pos.position_type != "currency":
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
        s_row = print_content("share")
        s_row = print_content("bond")
        s_row = print_content("etf")
        s_row = print_content("Other")
        last_row = print_content("currency")
        worksheet_port.autofilter(4, s_col, last_row, s_col+16)
        print_totals(last_row, s_col)

        return last_row

    def print_operations():
        logger.info('building operations table..')
        start_col = 1
        start_row = 2

        # Выводим строку расчета итогов
        n_ops = len(my_operations)
        end_line = start_row+n_ops+3
        worksheet_oplist.write(start_row, start_col+3, "ИТОГО:", cell_format['bold_right'])
        worksheet_oplist.write_formula(start_row, start_col+4,
                                       f"=SUBTOTAL(9, F6:F{end_line})",
                                       cell_format['right_number'])
        worksheet_oplist.write_formula(start_row, start_col+6,
                                       f"=SUBTOTAL(9, H6:H{end_line})",
                                       cell_format["RUB"])

        start_row += 2
        # Выводим заголовки
        headers = [
            # ["Название столбца", ширина],
            ["Дата", 18],
            ["Тип операции", 35],
            ["Тикер", 15],
            ["figi", 18],
            ["Сумма", 15],
            ["Валюта", 8],
            ["Сумма в руб", 15],
            ["Статус", 8],
        ]
        print_headers(worksheet_oplist, start_col, start_row, headers)

        # заполняем список операций
        for operation in my_operations:
            start_row += 1
            # TODO: формат даты...
            worksheet_oplist.write(start_row, start_col,
                                   operation.op_date,
                                   cell_format['date_time'])
            worksheet_oplist.write(start_row, start_col+1, operation.op_type)
            if operation.op_ticker is not None and operation.op_ticker != "None":
                worksheet_oplist.write(start_row, start_col+2, operation.op_ticker)
            worksheet_oplist.write(start_row, start_col+3, operation.op_figi)
            worksheet_oplist.write(start_row, start_col+4,
                                   operation.op_payment.ammount,
                                   cell_format[operation.op_currency])
            worksheet_oplist.write(start_row, start_col+5,
                                   operation.op_currency)
            worksheet_oplist.write(start_row, start_col+6,
                                   operation.op_payment_rub,
                                   cell_format['RUB'])
            worksheet_oplist.write(start_row, start_col+7, operation.op_status)

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
            if operation.op_type in ['Выплата купонов', 'Выплата дивидендов']:
                if operation.op_date.strftime('%Y') not in years:
                    years.append(operation.op_date.strftime('%Y'))

        operations_in_last_12_months = []  # needed for dividend salary

        for year in years:
            # header 1 - year
            worksheet_divs.merge_range(start_row, start_col, start_row, start_col + 4, year, merge_format['bold_center'])
            # header 2 - labels
            headers = [
                # ["Название столбца", ширина],
                ["Ticker", 14],
                ["Date", 14],
                ["Value", 14],
                ["Tax", 14],
                ["Value RUB", 14],
            ]
            start_row += 1
            print_headers(worksheet_divs, start_col, start_row, headers, False)
            start_row += 1

            # content
            operations_per_year = []
            for operation in my_operations:
                if operation.op_type in ['Выплата купонов', 'Выплата дивидендов']:
                    if operation.op_date.strftime('%Y') == year:
                        # print ticker
                        worksheet_divs.write(start_row, start_col,
                                             operation.op_ticker,
                                             cell_format['left'])
                        # print date
                        worksheet_divs.write(start_row, start_col + 1,
                                             operation.op_date.strftime('%Y %b %d'),
                                             cell_format['center'])
                        # print value
                        if operation.op_currency in supported_currencies:
                            worksheet_divs.write(start_row, start_col + 2, operation.op_payment.ammount, cell_format[operation.op_currency])
                        else:
                            worksheet_divs.write(start_row, start_col + 2, 'unknown currency', cell_format['right'])
                        # print tax
                        tax_payment = 0
                        for tax_op in my_operations:
                            if tax_op.op_type in ['Удержание налога по купонам',
                                                  'Удержание налога по дивидендам']:
                                if tax_op.op_ticker == operation.op_ticker and tax_op.op_date.strftime('%Y %b %d') == \
                                        operation.op_date.strftime('%Y %b %d'):
                                    tax_payment = tax_op.op_payment.ammount
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

    def print_iis_deduction_table():
        if sum_profile['broker_account_type'] != "TinkoffIis":
            logger.debug("account is not of IIS Type")
            worksheet_deduct.hide()
            return
        logger.info("printing IIS deductions table")

        start_col = 1
        start_row = 3
        # Headers
        worksheet_deduct.merge_range(start_row-2, start_col,
                                   start_row-2, start_col + 3,
                                   "Расчет налогового вычета ИИС", merge_format['bold_center'])
        worksheet_deduct.set_column(start_col + 1, start_col + 3, 13)
        # worksheet_deduct.write(start_row, start_col, 'Year', cell_format['bold_center'])
        worksheet_deduct.write(start_row, start_col + 1, 'PayIns', cell_format['bold_center'])
        worksheet_deduct.write(start_row, start_col + 2, 'Tax Base', cell_format['bold_center'])
        worksheet_deduct.write(start_row, start_col + 3, 'Deduction', cell_format['bold_center'])

        start_row += 1

        year_sums = sum_profile['iis_deduction']

        for year in sorted(year_sums.keys(), reverse=True):
            if year == 0:
                continue
            payin = year_sums[year]['pay_in']
            base = year_sums[year]['base']
            deduct = year_sums[year]['deduct']

            worksheet_deduct.write(start_row, start_col, year, cell_format['bold_center'])
            worksheet_deduct.write(start_row, start_col + 1, payin, cell_format['RUB'])
            worksheet_deduct.write(start_row, start_col + 2, base, cell_format['RUB'])
            worksheet_deduct.write(start_row, start_col + 3, deduct, cell_format['RUB'])
            start_row += 1

        # for the line on cell top
        deduct_total = year_sums[0]
        worksheet_deduct.write(start_row, start_col + 1, "", cell_format['RUB-bold-total'])
        worksheet_deduct.write(start_row, start_col + 2, "", cell_format['RUB-bold-total'])
        worksheet_deduct.write(start_row, start_col + 3, deduct_total, cell_format['RUB-bold-total'])

    def print_parts():
        logger.info('printing portfolio parts statistics...')

        start_col = 1
        start_row = 6

        # Считаем сколько строк займет табличка частей
        total = 0
        for currency in supported_currencies:
            if currency not in sum_profile['parts'].keys():
                continue
            total += len(sum_profile['parts'][currency].keys())+1

        # Comments in header
        worksheet_parts.merge_range(2, 1, 2, 6,
                                    'Структура долей активов',
                                    merge_format['bold_center'])
        worksheet_parts.merge_range(4, 1, 4, 6,
                                    '* - расчет по курсу ЦБ на текущую дату',
                                    merge_format['left_small'])
        worksheet_parts.merge_range(start_row+total, start_col, start_row+total, start_col+3,
                                    'Данные для формирования диаграммы',
                                    merge_format['bold_left'])
        worksheet_parts.merge_range(start_row+total+1, start_col, start_row+total+1, start_col+3,
                                    'Выделить и выбрать диаграмму "Солнечные лучи/',
                                    merge_format['left_small'])
        worksheet_parts.merge_range(start_row+total+2, start_col, start_row+total+2, start_col+3,
                                    'Sunburst" или "Дерево/Treemap"',
                                    merge_format['left_small'])
        # xlsxwriter не позволяет делать sunburst или treemap диаграммы :(

        # начальная строка для вывода данных для диаграмм по типу лучей солнца/Sunburst
        # или Дерева/Treemap - к сожалению только таблица данных, xlsxwriter их не вставляет
        chart_data_row = start_row+total + 2

        # header - labels
        headers = [
            ["Value", 14],
            ["Value RUB", 14],
            ["Currency", 12],
            ["Total %", 12],
        ]
        print_headers(worksheet_parts, start_col + 2, start_row, headers, False)
        worksheet_parts.set_column(start_col+2, start_col + 3, 14, cell_format['right'])

        start_row += 1
        cell_format['perc'] = workbook.add_format({'num_format': '0.0  ',
                                                   'font_color': get_color(5)})  # >0 for green
        cell_format['perc-bold'] = workbook.add_format({'num_format': '0.0 %', 'bold': True,
                                                        'font_color': get_color(5),  # >0 for green
                                                        'align': 'center'})
        for currency in supported_currencies:
            if currency not in sum_profile['parts'].keys():
                continue
            data = sum_profile['parts'][currency]
            worksheet_parts.write(start_row, start_col, currency, cell_format['bold_center'])
            worksheet_parts.write(start_row+1, start_col, data['totalPart'], cell_format['perc-bold'])

            for type in assets_types:
                worksheet_parts.write(start_row, start_col + 1, type, cell_format['bold_center'])
                if type not in data.keys():
                    # start_row += 1 # Если печатать строки с отсутствующими типами активов
                    continue
                type_data = data[type]

                worksheet_parts.write(start_row, start_col + 2, type_data['value'], cell_format[currency])
                worksheet_parts.write(start_row, start_col + 3, type_data['valueRub'], cell_format['RUB'])
                worksheet_parts.write(start_row, start_col + 4, type_data['currencyPart'], cell_format['perc'])
                worksheet_parts.write(start_row, start_col + 5, type_data['totalPart'], cell_format['perc'])

                # data for chart
                worksheet_parts.write(chart_data_row, start_col, currency, cell_format['bold_center'])
                worksheet_parts.write(chart_data_row, start_col + 1, type, cell_format['bold_center'])
                worksheet_parts.write(chart_data_row, start_col + 2, type_data['valueRub'], cell_format['RUB'])

                start_row += 1
                chart_data_row += 1

            # Totals for the currency
            worksheet_parts.write(start_row, start_col + 2,
                                  data['value'], cell_format[f'{currency}-bold-total'])
            worksheet_parts.write(start_row, start_col + 3,
                                  data['valueRub'], cell_format['RUB-bold-total'])
            # worksheet_parts.write(start_row, start_col + 4, type_data['currencyPart'], cell_format['perc'])

            start_row += 3  # пропуск между валютами

        start_col += 8
        start_row = 6
        # Table 2 - headers
        for i, type in enumerate(assets_types):
            worksheet_parts.write(start_row, start_col + 1 + i, type, cell_format['bold_center'])
        start_row += 1
        pie_data_start_row = start_row  # сохраняем строку с началом данных для графиков
        currency_count_for_chart = 0  # пересчитаем количество валют, чтобы потом выводить графики

        for currency in supported_currencies:
            if currency not in sum_profile['parts'].keys():
                continue
            data = sum_profile['parts'][currency]
            worksheet_parts.write(start_row, start_col, currency, cell_format['bold_center'])

            for i, type in enumerate(assets_types):
                if type not in data.keys():
                    continue
                type_data = data[type]
                worksheet_parts.write(start_row, start_col + 1 + i, type_data['totalPart'], cell_format['perc'])

            worksheet_parts.write(start_row, start_col + 2 + i, data['totalPart'], cell_format['perc-bold'])
            start_row += 1
            currency_count_for_chart += 1
        # Итоговая строка
        for i, type in enumerate(assets_types):
            if type not in sum_profile['parts'].keys():
                continue
            type_data = sum_profile['parts'][type]
            worksheet_parts.write(start_row, start_col + 1 + i, type_data['totalPart'], cell_format['perc-bold'])

        # Круговая диаграмма - структура активов по Валютам
        chart = workbook.add_chart({'type': 'pie'})
        chart.set_title({'name': 'Структура активов по валютам'})
        data_col = start_col + len(assets_types) + 1 # следующая колонка после активов
        chart.add_series({
            'name': 'Валюты и их доли',
            'categories': ['Parts', pie_data_start_row, start_col,
                                    pie_data_start_row + currency_count_for_chart-1, start_col],
            'values': ['Parts', pie_data_start_row, data_col,
                                pie_data_start_row + currency_count_for_chart-1, data_col],
            'data_labels': {'value': True, 'category': True, 'separator': "\n"},
        })
        worksheet_parts.insert_chart(start_row+2, start_col, chart)

        # Гистограмма с накоплением - труктура активов по типам и валютам
        chart2 = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})
        chart2.set_title({'name': 'Структура активов по типам и валютам'})
        categories = ['Parts', pie_data_start_row-1, start_col+1, pie_data_start_row-1, start_col+5]
        for i in range(pie_data_start_row, pie_data_start_row+currency_count_for_chart):
            chart2.add_series({
                'name': ['Parts', i, start_col, i, start_col],
                'categories': categories,
                'values': ['Parts', i, start_col+1, i, start_col+5],
                'data_labels': {'value': True},
                'gap': 60,
            })
        worksheet_parts.insert_chart(start_row+17, start_col, chart2)

    def print_clarification(s_row, s_col ):
        logger.info('printing clarification..')
        n = 0
        lines = [
            # ['заглавие', 'описание', кол-во дополнительных строк после],
            ['name', 'название инструмента', 0],
            ['ticker', 'тикер инструмента', 0],
            ['balance', 'количество бумаг в портфеле', 0],
            ['currency', 'валюта', 0],
            ['ave.price', 'средняя цена покупки одной бумаги', 0],
            ['sum.buy', 'стоимость приобретения. = ave.price * balance', 0],
            ['exp.yield', 'ожидаемый доход при полном закрытии позиции', 0],
            ['market price', 'рыночная цена одной бумаги. Берётся из API,'
                             ' но для облигаций = market value / balance', 0],
            ['% change', 'изменение рыночной стоимости одной бумаги относительно её ave.price', 0],
            ['market value', 'рыночная стоимость всей позиции в портфеле', 0],
            ['market value RUB', 'market value в рублях по рыночному курсу', 1],

            ['CB value RUB', 'тоже market value в рублях, но по курсу ЦБ на сегодня', 0],
            ['ave.buy in RUB', 'средняя цена покупки в рублях по курсу ЦБ на день покупки.'
                               ' Рассчитывается сложно', 0],
            ['sum.buy in RUB', 'сумма покупки всей позиции в рублях по курсу ЦБ.'
                               ' = ave.buy in RUB * balance', 0],
            ['tax base', 'налоговая база. Разница между текущей рыночной стоимостью позиции '
                         'в рублях по курсу ЦБ и стоимостью её приобретения.'
                         '= CB value RUB - sum.buy in RUB', 0],
            ['expected tax', 'ожидаемый налог. = tax.base * 13%. Не учитывает налоговые льготы и'
                             'налог, который мог уже набежать по ранее закрытым позициям', 1],

            ['Investing period', 'период инвестирования. Сколько лет, месяцев, дней с даты,'
                                 'которая указана в my_account.txt до сегодняшнего дня', 0],
            ['PayIn - PayOut', 'разница между заведёнными на счёт средствами и выведенными. ', 0],
            ['Commissions payed', 'сумма всех уплаченных комиссий'
                                  ' (За торговлю и за обслуживаение)', 0],
            ['Taxes payed', 'сумма всех уплаченных налогов'
                            ' (Закрытие позиций, купоны и дивиденды)', 0],
            ['Clean portfolio', ' - стоимость портфеля, очищенная от налога, '
                                'начисляемого при закрытии всех позиций. '
                                'Не учитывает возможные льготы и те налоги,'
                                ' которые уже могли набежать по ранее закрытым позициям, '
                                'а также самостоятельно декларируемые налоги', 0],
            ['Profit', 'почти чистая прибыль. = Clean portfolio - (PayIn - PayOut)', 0],
            ['XIRR', 'the irregular internal rate of return. Показатель на основе формулы Excel, '
                     'которая рассчитывает эффективность инвестирования '
                     'с учётом всех пополнений и выводов средств', 3],

            ['', ' Разработано @softandiron и контрибьюторами. Версия v3.x, 2022 год.', 0],
            ['', ' GitHub: https://github.com/softandiron/tinkproject', 0]
        ]

        for line in lines:
            worksheet_port.write(s_row + n, s_col, line[0], cell_format['bold_right'])
            worksheet_port.merge_range(s_row + n, s_col + 1, s_row + n, s_col + 16,
                                       '  ' + line[1],
                                       merge_format['left'])
            n += 1 + line[2]

    last_row_pos = print_portfolio(1, 1)
    print_operations()
    print_statistics(last_row_pos + 3, 1)
    print_clarification(last_row_pos + 18, 1)
    print_dividends_and_coupons()
    print_iis_deduction_table()
    print_parts()

    # finish Excel
    logger.info('Excel file composed! With name: '+excel_file_name)
    workbook.close()


config = Config()
