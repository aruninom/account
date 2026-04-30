import base64
import io

import xlsxwriter
from odoo import fields, models


class ExcelReportMixin(models.AbstractModel):
    _name = 'excel.report.mixin'
    _description = 'Excel Report Mixin'

    def _create_excel_attachment(self, filename, builder):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        builder(workbook)
        workbook.close()
        output.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


class AccountPartnerLedgerExcel(models.TransientModel):
    _inherit = 'account.report.partner.ledger'

    def action_print_excel(self):
        self.ensure_one()
        data = {'form': self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'reconciled', 'amount_currency', 'result_selection'])[0]}
        data['form']['used_context'] = dict(self._build_contexts(data), lang=self.env.context.get('lang') or 'en_US')
        data['computed'] = {}
        report_model = self.env['report.base_accounting_kit.report_partnerledger']
        values = report_model._get_report_values([], data=data)

        def build(workbook):
            ws = workbook.add_worksheet('Partner Ledger')
            h = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
            b = workbook.add_format({'border': 1})
            m = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
            row = 0
            ws.write_row(row, 0, ['Partner', 'Date', 'Entry', 'Debit', 'Credit', 'Balance'], h)
            row += 1
            for partner in values['docs']:
                for line in values['lines'](data, partner):
                    ws.write(row, 0, partner.name or '', b)
                    ws.write(row, 1, fields.Date.to_string(line.get('date')) if line.get('date') else '', b)
                    ws.write(row, 2, line.get('displayed_name', ''), b)
                    ws.write_number(row, 3, float(line.get('debit', 0.0)), m)
                    ws.write_number(row, 4, float(line.get('credit', 0.0)), m)
                    ws.write_number(row, 5, float(line.get('progress', 0.0)), m)
                    row += 1
            ws.set_column('A:C', 30)
            ws.set_column('D:F', 18)

        return self.env['excel.report.mixin']._create_excel_attachment('Partner Ledger.xlsx', build)


class AccountBankBookExcel(models.TransientModel):
    _inherit = 'account.bank.book.report'

    def action_print_excel(self):
        self.ensure_one()
        data = {'form': self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'display_account', 'account_ids', 'sortby', 'initial_balance'])[0]}
        data['form']['used_context'] = dict(self._build_contexts(data), lang=self.env.context.get('lang') or 'en_US')
        values = self.env['report.base_accounting_kit.report_bank_book'].with_context(data['form']['used_context'])._get_report_values([], data=data)

        def build(workbook):
            ws = workbook.add_worksheet('Bank Book')
            h = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
            b = workbook.add_format({'border': 1})
            m = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
            row = 0
            ws.write_row(row, 0, ['Account', 'Date', 'Journal', 'Label', 'Debit', 'Credit', 'Balance'], h)
            row += 1
            for acc in values['Accounts']:
                for line in acc.get('move_lines', []):
                    ws.write(row, 0, f"{acc.get('code','')} {acc.get('name','')}", b)
                    ws.write(row, 1, fields.Date.to_string(line.get('ldate')) if line.get('ldate') else '', b)
                    ws.write(row, 2, line.get('lcode', ''), b)
                    ws.write(row, 3, line.get('lname', ''), b)
                    ws.write_number(row, 4, float(line.get('debit', 0.0)), m)
                    ws.write_number(row, 5, float(line.get('credit', 0.0)), m)
                    ws.write_number(row, 6, float(line.get('balance', 0.0)), m)
                    row += 1
        return self.env['excel.report.mixin']._create_excel_attachment('Bank Book.xlsx', build)


class AccountCashBookExcel(models.TransientModel):
    _inherit = 'account.cash.book.report'

    def action_print_excel(self):
        self.ensure_one()
        data = {'form': self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'display_account', 'account_ids', 'sortby', 'initial_balance'])[0]}
        data['form']['used_context'] = dict(self._build_contexts(data), lang=self.env.context.get('lang') or 'en_US')
        values = self.env['report.base_accounting_kit.report_cash_book'].with_context(data['form']['used_context'])._get_report_values([], data=data)
        def build(workbook):
            ws = workbook.add_worksheet('Cash Book')
            h = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
            b = workbook.add_format({'border': 1})
            m = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
            row = 0
            ws.write_row(row, 0, ['Account', 'Date', 'Journal', 'Label', 'Debit', 'Credit', 'Balance'], h)
            row += 1
            for acc in values['Accounts']:
                for line in acc.get('move_lines', []):
                    ws.write(row, 0, f"{acc.get('code','')} {acc.get('name','')}", b)
                    ws.write(row, 1, fields.Date.to_string(line.get('ldate')) if line.get('ldate') else '', b)
                    ws.write(row, 2, line.get('lcode', ''), b)
                    ws.write(row, 3, line.get('lname', ''), b)
                    ws.write_number(row, 4, float(line.get('debit', 0.0)), m)
                    ws.write_number(row, 5, float(line.get('credit', 0.0)), m)
                    ws.write_number(row, 6, float(line.get('balance', 0.0)), m)
                    row += 1
        return self.env['excel.report.mixin']._create_excel_attachment('Cash Book.xlsx', build)


class AccountDayBookExcel(models.TransientModel):
    _inherit = 'account.day.book.report'

    def action_print_excel(self):
        self.ensure_one()
        data = {'form': self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'account_ids'])[0]}
        data['form']['used_context'] = dict(self._build_contexts(data), lang=self.env.context.get('lang') or 'en_US')
        values = self.env['report.base_accounting_kit.day_book_report_template']._get_report_values([], data=data)

        def build(workbook):
            ws = workbook.add_worksheet('Day Book')
            h = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
            b = workbook.add_format({'border': 1})
            m = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
            row = 0
            ws.write_row(row, 0, ['Date', 'Account', 'Journal', 'Label', 'Debit', 'Credit', 'Balance'], h)
            row += 1
            for day in values['Accounts']:
                for line in day.get('child_lines', []):
                    ws.write(row, 0, fields.Date.to_string(line.get('ldate')) if line.get('ldate') else '', b)
                    ws.write(row, 1, line.get('accname', ''), b)
                    ws.write(row, 2, line.get('lcode', ''), b)
                    ws.write(row, 3, line.get('lname', ''), b)
                    ws.write_number(row, 4, float(line.get('debit', 0.0)), m)
                    ws.write_number(row, 5, float(line.get('credit', 0.0)), m)
                    ws.write_number(row, 6, float(line.get('balance', 0.0)), m)
                    row += 1
        return self.env['excel.report.mixin']._create_excel_attachment('Day Book.xlsx', build)


class CashFlowReportExcel(models.TransientModel):
    _inherit = 'cash.flow.report'

    def action_print_excel(self):
        self.ensure_one()
        data = {'form': self.read(['date_from', 'enable_filter', 'debit_credit', 'date_to', 'account_report_id', 'target_move', 'company_id', 'journal_ids', 'filter_cmp', 'date_from_cmp', 'date_to_cmp'])[0]}
        data['form']['used_context'] = dict(self._build_contexts(data), lang=self.env.context.get('lang') or 'en_US')
        data['form']['comparison_context'] = self._build_comparison_context({'form': data['form']})
        lines = self.env['report.base_accounting_kit.report_cash_flow'].with_context(data['form']['used_context']).get_account_lines(data['form'])

        def build(workbook):
            ws = workbook.add_worksheet('Cash Flow')
            h = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
            b = workbook.add_format({'border': 1})
            m = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
            row = 0
            ws.write_row(row, 0, ['Particulars', 'Debit', 'Credit', 'Balance'], h)
            row += 1
            for line in lines:
                ws.write(row, 0, ('    ' * max(line.get('level', 1) - 1, 0)) + (line.get('name') or ''), b)
                ws.write_number(row, 1, float(line.get('debit', 0.0)), m)
                ws.write_number(row, 2, float(line.get('credit', 0.0)), m)
                ws.write_number(row, 3, float(line.get('balance', 0.0)), m)
                row += 1
        return self.env['excel.report.mixin']._create_excel_attachment('Cash Flow Statement.xlsx', build)
