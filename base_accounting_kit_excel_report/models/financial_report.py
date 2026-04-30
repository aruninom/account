import base64
import io

import xlsxwriter
from odoo import fields, models


class FinancialReport(models.TransientModel):
    _inherit = 'financial.report'

    def action_print_excel(self):
        self.ensure_one()

        data = {
            'ids': self.env.context.get('active_ids', []),
            'model': self.env.context.get('active_model', 'ir.ui.menu'),
            'form': self.read([
                'date_from', 'enable_filter', 'debit_credit', 'date_to',
                'account_report_id', 'target_move', 'view_format', 'company_id'
            ])[0],
        }

        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(
            used_context,
            lang=self.env.context.get('lang') or 'en_US',
        )

        report_lines = self.get_account_lines(data['form'])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Financial Report')

        title_format = workbook.add_format({'bold': True, 'font_size': 14})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
        money_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        text_format = workbook.add_format({'border': 1})
        level_bold_format = workbook.add_format({'border': 1, 'bold': True})

        company_name = self.company_id.name or ''
        report_name = self.account_report_id.name or 'Financial Report'
        date_from = fields.Date.to_string(self.date_from) if self.date_from else ''
        date_to = fields.Date.to_string(self.date_to) if self.date_to else ''

        sheet.merge_range('A1:D1', company_name, title_format)
        sheet.merge_range('A2:D2', report_name, title_format)
        sheet.write('A3', 'From:')
        sheet.write('B3', date_from)
        sheet.write('C3', 'To:')
        sheet.write('D3', date_to)

        row = 5
        sheet.write(row, 0, 'Particulars', header_format)
        sheet.write(row, 1, 'Debit', header_format)
        sheet.write(row, 2, 'Credit', header_format)
        sheet.write(row, 3, 'Balance', header_format)
        row += 1

        def _safe_int(value, default=1):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        def _safe_float(value, default=0.0):
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        for line in report_lines:
            level = _safe_int(line.get('level', 1), default=1)
            name = ('    ' * max(level - 1, 0)) + (line.get('name') or '')
            line_format = level_bold_format if line.get('type') == 'report' else text_format

            sheet.write(row, 0, name, line_format)
            sheet.write_number(row, 1, _safe_float(line.get('debit', 0.0)), money_format)
            sheet.write_number(row, 2, _safe_float(line.get('credit', 0.0)), money_format)
            sheet.write_number(row, 3, _safe_float(line.get('balance', 0.0)), money_format)
            row += 1

        sheet.set_column('A:A', 45)
        sheet.set_column('B:D', 18)

        workbook.close()
        output.seek(0)

        filename = f"{report_name.replace('/', '-')}.xlsx"
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
