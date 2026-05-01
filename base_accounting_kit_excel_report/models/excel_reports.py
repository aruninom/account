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
        attachment_vals = {
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }
        active_id = self.env.context.get('active_id') or (self.env.context.get('active_ids') or [False])[0]
        if self.env.context.get('active_model') and active_id:
            attachment_vals.update({
                'res_model': self.env.context['active_model'],
                'res_id': active_id,
            })

        attachment = self.env['ir.attachment'].create(attachment_vals)
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


class AccountPartnerLedgerExcel(models.TransientModel):
    _inherit = 'account.report.partner.ledger'

    def action_print_excel_kit(self):
        self.ensure_one()
        data = {'form': self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'reconciled', 'amount_currency', 'result_selection'])[0]}
        data['form']['used_context'] = dict(self._build_contexts(data), lang=self.env.context.get('lang') or 'en_US')
        data['computed'] = {}
        report_model = self.env['report.base_accounting_kit.report_partnerledger'].with_context(active_model=self._name, active_id=self.id, active_ids=self.ids)
        values = report_model._get_report_values(self.ids, data=data)

        def build(workbook):
            ws = workbook.add_worksheet('Partner Ledger')
            title = workbook.add_format({'bold': True, 'font_size': 18})
            sub_h = workbook.add_format({'bold': True})
            head = workbook.add_format({'bottom': 1})
            txt = workbook.add_format({})
            money = workbook.add_format({'num_format': '#,##0.00'})

            row = 1
            ws.write(row, 0, 'Partner Ledger', title)
            row += 2
            ws.write(row, 0, 'Company:', sub_h)
            ws.write(row, 1, self.company_id.name or '', txt)
            ws.write(row, 4, 'Target Moves:', sub_h)
            ws.write(row, 5, 'All Posted Entries' if self.target_move == 'posted' else 'All Entries', txt)
            row += 1
            if self.date_from:
                ws.write(row, 0, 'Date from :', sub_h)
                ws.write(row, 1, fields.Date.to_string(self.date_from), txt)
            if self.date_to:
                ws.write(row, 2, 'Date to :', sub_h)
                ws.write(row, 3, fields.Date.to_string(self.date_to), txt)
            row += 2

            headers = ['Date', 'JRNL', 'Ref', 'Debit', 'Credit', 'Balance']
            if self.amount_currency:
                headers.append('Currency')
            ws.write_row(row, 0, headers, head)
            row += 1

            for partner in values['docs']:
                ws.write(row, 0, f"{partner.ref or ''} - {partner.name or ''}", sub_h)
                ws.write_number(row, 3, float(values['sum_partner'](data, partner, 'debit') or 0.0), money)
                ws.write_number(row, 4, float(values['sum_partner'](data, partner, 'credit') or 0.0), money)
                ws.write_number(row, 5, float(values['sum_partner'](data, partner, 'debit - credit') or 0.0), money)
                row += 1
                for line in values['lines'](data, partner):
                    ws.write(row, 0, fields.Date.to_string(line.get('date')) if line.get('date') else '', txt)
                    ws.write(row, 1, line.get('code', ''), txt)
                    ws.write(row, 2, line.get('displayed_name') or '', txt)
                    ws.write_number(row, 3, float(line.get('debit', 0.0)), money)
                    ws.write_number(row, 4, float(line.get('credit', 0.0)), money)
                    ws.write_number(row, 5, float(line.get('progress', 0.0)), money)
                    if self.amount_currency:
                        ws.write_number(row, 6, float(line.get('amount_currency') or 0.0), money)
                    row += 1

            ws.set_column('A:C', 24)
            ws.set_column('D:G', 16)
        return self.env['excel.report.mixin']._create_excel_attachment('Partner Ledger.xlsx', build)

    def action_print_excel(self):
        return self.action_print_excel_kit()


class AccountGeneralLedgerExcel(models.TransientModel):
    _inherit = 'account.report.general.ledger'

    def action_print_excel_kit(self):
        self.ensure_one()
        data = {'form': self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'display_account', 'sortby', 'initial_balance'])[0]}
        data['form']['used_context'] = dict(self._build_contexts(data), lang=self.env.context.get('lang') or 'en_US')
        values = self.env['report.base_accounting_kit.report_general_ledger'].with_context(
            active_model=self._name,
            active_id=self.id,
            active_ids=self.ids,
        )._get_report_values(self.ids, data=data)

        def build(workbook):
            ws = workbook.add_worksheet('General Ledger')
            title = workbook.add_format({'bold': True, 'font_size': 14})
            sub_h = workbook.add_format({'bold': True})
            h = workbook.add_format({'bottom': 1})
            b = workbook.add_format({})
            m = workbook.add_format({'num_format': '#,##0.00'})

            display_map = {
                'all': "All accounts'",
                'movement': 'With movements',
                'not_zero': 'With balance not equal to zero',
            }
            row = 0
            ws.write(row, 0, f"{self.company_id.name or ''}: General ledger", title)
            row += 2
            ws.write(row, 0, 'Journals:', sub_h)
            ws.write(row, 1, ', '.join(values.get('print_journal', [])))
            ws.write(row, 4, 'Display Account', sub_h)
            ws.write(row, 5, display_map.get(self.display_account, self.display_account or ''))
            ws.write(row, 7, 'Target Moves:', sub_h)
            ws.write(row, 8, 'All Posted Entries' if self.target_move == 'posted' else 'All Entries')
            row += 2
            ws.write(row, 0, 'Sorted By:', sub_h)
            ws.write(row, 1, 'Date' if self.sortby == 'sort_date' else 'Journal and Partner')
            if self.date_from:
                ws.write(row, 4, 'Date from :', sub_h)
                ws.write(row, 5, fields.Date.to_string(self.date_from))
            if self.date_to:
                ws.write(row, 7, 'Date to :', sub_h)
                ws.write(row, 8, fields.Date.to_string(self.date_to))
            row += 2

            ws.write_row(row, 0, ['Date', 'JRNL', 'Partner', 'Ref', 'Move', 'Entry Label', 'Debit', 'Credit', 'Balance', 'Currency'], h)
            row += 1
            for acc in values.get('Accounts', []):
                ws.write(row, 0, f"{acc.get('code', '')} {acc.get('name', '')}", sub_h)
                ws.write_number(row, 6, float(acc.get('debit') or 0.0), m)
                ws.write_number(row, 7, float(acc.get('credit') or 0.0), m)
                ws.write_number(row, 8, float(acc.get('balance') or 0.0), m)
                row += 1
                for line in acc.get('move_lines', []):
                    ws.write(row, 0, fields.Date.to_string(line.get('ldate')) if line.get('ldate') else '', b)
                    ws.write(row, 1, line.get('lcode', ''), b)
                    ws.write(row, 2, line.get('partner_name', ''), b)
                    ws.write(row, 3, line.get('lref', ''), b)
                    ws.write(row, 4, line.get('move_name', ''), b)
                    ws.write(row, 5, line.get('lname', ''), b)
                    ws.write_number(row, 6, float(line.get('debit') or 0.0), m)
                    ws.write_number(row, 7, float(line.get('credit') or 0.0), m)
                    ws.write_number(row, 8, float(line.get('balance') or 0.0), m)
                    currency_text = ''
                    if line.get('amount_currency'):
                        currency_text = f"{line.get('amount_currency')} {line.get('currency_code') or ''}".strip()
                    ws.write(row, 9, currency_text, b)
                    row += 1

            ws.set_column('A:F', 18)
            ws.set_column('G:I', 14)
            ws.set_column('J:J', 18)
        return self.env['excel.report.mixin']._create_excel_attachment('General Ledger.xlsx', build)

    def action_print_excel(self):
        return self.action_print_excel_kit()


class AccountBankBookExcel(models.TransientModel):
    _inherit = 'account.bank.book.report'

    def action_print_excel(self):
        self.ensure_one()
        data = {'form': self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'display_account', 'sortby', 'initial_balance'])[0]}
        data['form']['used_context'] = dict(self._build_contexts(data), lang=self.env.context.get('lang') or 'en_US')
        values = self.env['report.base_accounting_kit.report_bank_book'].with_context(data['form']['used_context'], active_model=self._name, active_id=self.id, active_ids=self.ids)._get_report_values(self.ids, data=data)

        def build(workbook):
            ws = workbook.add_worksheet('Bank Book')
            title = workbook.add_format({'bold': True, 'font_size': 14})
            sub_h = workbook.add_format({'bold': True})
            h = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
            b = workbook.add_format({'border': 1})
            m = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})

            row = 0
            ws.merge_range(row, 0, row, 9, f"{self.company_id.name or ''}: Bank Book Report", title)
            row += 2
            ws.write(row, 0, 'Journals:', sub_h)
            ws.write(row, 1, ', '.join(values.get('print_journal', [])))
            ws.write(row, 4, 'Display Account', sub_h)
            ws.write(row, 5, 'With movements')
            ws.write(row, 7, 'Target Moves:', sub_h)
            ws.write(row, 8, 'All Posted Entries' if self.target_move == 'posted' else 'All Entries')
            row += 2
            ws.write(row, 0, 'Sorted By:', sub_h)
            ws.write(row, 1, 'Date' if self.sortby == 'sort_date' else 'Journal & Partner')
            ws.write(row, 7, 'Date from :', sub_h)
            ws.write(row, 8, fields.Date.to_string(self.date_from) if self.date_from else '')
            row += 1
            ws.write(row, 7, 'Date to :', sub_h)
            ws.write(row, 8, fields.Date.to_string(self.date_to) if self.date_to else '')
            row += 2

            ws.write_row(row, 0, ['Date', 'JRNL', 'Partner', 'Ref', 'Move', 'Entry Label', 'Debit', 'Credit', 'Balance', 'Currency'], h)
            row += 1
            for acc in values.get('Accounts', []):
                for line in acc.get('move_lines', []):
                    ws.write(row, 0, fields.Date.to_string(line.get('ldate')) if line.get('ldate') else '', b)
                    ws.write(row, 1, line.get('lcode', ''), b)
                    ws.write(row, 2, line.get('partner_name', ''), b)
                    ws.write(row, 3, line.get('lref', ''), b)
                    ws.write(row, 4, line.get('move_name', ''), b)
                    ws.write(row, 5, line.get('lname', ''), b)
                    ws.write_number(row, 6, float(line.get('debit') or 0.0), m)
                    ws.write_number(row, 7, float(line.get('credit') or 0.0), m)
                    ws.write_number(row, 8, float(line.get('balance') or 0.0), m)
                    ws.write(row, 9, line.get('currency_code', ''), b)
                    row += 1
            ws.set_column('A:F', 18)
            ws.set_column('G:I', 14)
            ws.set_column('J:J', 12)
        return self.env['excel.report.mixin']._create_excel_attachment('Bank Book.xlsx', build)


class AccountCashBookExcel(models.TransientModel):
    _inherit = 'account.cash.book.report'

    def action_print_excel(self):
        self.ensure_one()
        data = {'form': self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'display_account', 'sortby', 'initial_balance'])[0]}
        data['form']['used_context'] = dict(self._build_contexts(data), lang=self.env.context.get('lang') or 'en_US')
        values = self.env['report.base_accounting_kit.report_cash_book'].with_context(data['form']['used_context'], active_model=self._name, active_id=self.id, active_ids=self.ids)._get_report_values(self.ids, data=data)
        def build(workbook):
            ws = workbook.add_worksheet('Cash Book')
            title = workbook.add_format({'bold': True, 'font_size': 14})
            sub_h = workbook.add_format({'bold': True})
            h = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
            b = workbook.add_format({'border': 1})
            m = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})

            row = 0
            ws.merge_range(row, 0, row, 9, f"{self.company_id.name or ''}: Cash Book Report", title)
            row += 2
            ws.write(row, 0, 'Journals:', sub_h)
            ws.write(row, 1, ', '.join(values.get('print_journal', [])))
            ws.write(row, 4, 'Display Account', sub_h)
            ws.write(row, 5, 'With movements')
            ws.write(row, 7, 'Target Moves:', sub_h)
            ws.write(row, 8, 'All Posted Entries' if self.target_move == 'posted' else 'All Entries')
            row += 2
            ws.write(row, 0, 'Sorted By:', sub_h)
            ws.write(row, 1, 'Date' if self.sortby == 'sort_date' else 'Journal & Partner')
            ws.write(row, 7, 'Date from :', sub_h)
            ws.write(row, 8, fields.Date.to_string(self.date_from) if self.date_from else '')
            row += 1
            ws.write(row, 7, 'Date to :', sub_h)
            ws.write(row, 8, fields.Date.to_string(self.date_to) if self.date_to else '')
            row += 2

            ws.write_row(row, 0, ['Date', 'JRNL', 'Partner', 'Ref', 'Move', 'Entry Label', 'Debit', 'Credit', 'Balance', 'Currency'], h)
            row += 1
            for acc in values.get('Accounts', []):
                for line in acc.get('move_lines', []):
                    ws.write(row, 0, fields.Date.to_string(line.get('ldate')) if line.get('ldate') else '', b)
                    ws.write(row, 1, line.get('lcode', ''), b)
                    ws.write(row, 2, line.get('partner_name', ''), b)
                    ws.write(row, 3, line.get('lref', ''), b)
                    ws.write(row, 4, line.get('move_name', ''), b)
                    ws.write(row, 5, line.get('lname', ''), b)
                    ws.write_number(row, 6, float(line.get('debit') or 0.0), m)
                    ws.write_number(row, 7, float(line.get('credit') or 0.0), m)
                    ws.write_number(row, 8, float(line.get('balance') or 0.0), m)
                    ws.write(row, 9, line.get('currency_code', ''), b)
                    row += 1
            ws.set_column('A:F', 18)
            ws.set_column('G:I', 14)
            ws.set_column('J:J', 12)
        return self.env['excel.report.mixin']._create_excel_attachment('Cash Book.xlsx', build)


class AccountDayBookExcel(models.TransientModel):
    _inherit = 'account.day.book.report'

    def action_print_excel(self):
        self.ensure_one()
        data = {'form': self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'account_ids'])[0]}
        if data['form'].get('date_from'):
            data['form']['date_from'] = fields.Date.to_string(data['form']['date_from'])
        if data['form'].get('date_to'):
            data['form']['date_to'] = fields.Date.to_string(data['form']['date_to'])
        data['form']['used_context'] = dict(self._build_contexts(data), lang=self.env.context.get('lang') or 'en_US')
        values = self.env['report.base_accounting_kit.day_book_report_template'].with_context(active_model=self._name, active_id=self.id, active_ids=self.ids)._get_report_values(self.ids, data=data)

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


class AccountPrintJournalExcel(models.TransientModel):
    _inherit = 'account.print.journal'

    def action_print_excel(self):
        self.ensure_one()
        data = {'form': self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'sort_selection'])[0]}
        data['form']['used_context'] = dict(self._build_contexts(data), lang=self.env.context.get('lang') or 'en_US')
        values = self.env['report.base_accounting_kit.report_journal_audit'].with_context(active_model=self._name, active_id=self.id, active_ids=self.ids)._get_report_values(self.ids, data=data)

        def build(workbook):
            ws = workbook.add_worksheet('Journal Audit')
            h = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
            b = workbook.add_format({'border': 1})
            m = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
            row = 0
            ws.write_row(row, 0, ['Journal', 'Date', 'Entry', 'Account', 'Partner', 'Label', 'Debit', 'Credit'], h)
            row += 1
            for journal in values['docs']:
                for line in values['lines'].get(journal, self.env['account.move.line']):
                    ws.write(row, 0, journal.display_name or '', b)
                    ws.write(row, 1, fields.Date.to_string(line.date) if line.date else '', b)
                    ws.write(row, 2, line.move_id.name or '', b)
                    ws.write(row, 3, line.account_id.display_name or '', b)
                    ws.write(row, 4, line.partner_id.display_name or '', b)
                    ws.write(row, 5, line.name or '', b)
                    ws.write_number(row, 6, float(line.debit or 0.0), m)
                    ws.write_number(row, 7, float(line.credit or 0.0), m)
                    row += 1
            ws.set_column('A:F', 28)
            ws.set_column('G:H', 16)

        return self.env['excel.report.mixin']._create_excel_attachment('Journal Audit.xlsx', build)


class AccountAgedTrialBalanceExcel(models.TransientModel):
    _inherit = 'account.aged.trial.balance'

    def action_print_excel(self):
        self.ensure_one()
        data = {'form': self.read(['date_from', 'result_selection', 'target_move', 'period_length'])[0]}
        values = self.env['report.base_accounting_kit.report_agedpartnerbalance'].with_context(active_model=self._name, active_id=self.id, active_ids=self.ids)._get_report_values(self.ids, data=data)

        def build(workbook):
            ws = workbook.add_worksheet('Aged Partner Balance')
            h = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
            b = workbook.add_format({'border': 1})
            m = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
            row = 0
            ws.write_row(row, 0, ['Partner', 'Not Due', '0-30', '31-60', '61-90', '91-120', '+120', 'Total'], h)
            row += 1
            for line in values.get('get_partner_lines', []):
                ws.write(row, 0, line.get('name', ''), b)
                ws.write_number(row, 1, float(line.get('direction') or 0.0), m)
                ws.write_number(row, 2, float(line.get('4') or 0.0), m)
                ws.write_number(row, 3, float(line.get('3') or 0.0), m)
                ws.write_number(row, 4, float(line.get('2') or 0.0), m)
                ws.write_number(row, 5, float(line.get('1') or 0.0), m)
                ws.write_number(row, 6, float(line.get('0') or 0.0), m)
                ws.write_number(row, 7, float(line.get('total') or 0.0), m)
                row += 1

        return self.env['excel.report.mixin']._create_excel_attachment('Aged Partner Balance.xlsx', build)


class AccountTrialBalanceExcel(models.TransientModel):
    _inherit = 'account.balance.report'

    def action_print_excel(self):
        self.ensure_one()
        data = {'form': self.read(['date_from', 'date_to', 'target_move', 'display_account'])[0]}
        data['form']['used_context'] = dict(self._build_contexts(data), lang=self.env.context.get('lang') or 'en_US')
        values = self.env['report.base_accounting_kit.report_trial_balance'].with_context(active_model=self._name, active_id=self.id, active_ids=self.ids)._get_report_values(self.ids, data=data)

        def build(workbook):
            ws = workbook.add_worksheet('Trial Balance')
            h = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
            b = workbook.add_format({'border': 1})
            m = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
            row = 0
            ws.write_row(row, 0, ['Code', 'Account', 'Debit', 'Credit', 'Balance'], h)
            row += 1
            for acc in values.get('Accounts', []):
                ws.write(row, 0, acc.get('code', ''), b)
                ws.write(row, 1, acc.get('name', ''), b)
                ws.write_number(row, 2, float(acc.get('debit') or 0.0), m)
                ws.write_number(row, 3, float(acc.get('credit') or 0.0), m)
                ws.write_number(row, 4, float(acc.get('balance') or 0.0), m)
                row += 1

        return self.env['excel.report.mixin']._create_excel_attachment('Trial Balance.xlsx', build)


class AccountGeneralLedgerExcelSafe(models.TransientModel):
    _inherit = 'account.report.general.ledger'

    def action_print_excel(self):
        """Safety override: always route button to the kit method."""
        return self.action_print_excel_kit()
