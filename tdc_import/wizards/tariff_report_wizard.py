# -*- coding: utf-8 -*-
import io
import base64

from odoo import models, fields


class TdcImportTariffReportWizard(models.TransientModel):
    _name = 'tdc.import.tariff.report.wizard'
    _description = 'Tariff Excel Report Wizard'

    date_from = fields.Date(string='GD Date From')
    date_to = fields.Date(string='GD Date To')
    partner_id = fields.Many2one('res.partner', string='Vendor')

    def _get_tariffs(self):
        domain = []
        if self.date_from:
            domain.append(('gd_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('gd_date', '<=', self.date_to))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        return self.env['tdc.import.tariff'].search(domain, order='gd_date')

    def action_export_xlsx(self):
        self.ensure_one()
        import xlsxwriter  # bundled with Odoo

        tariffs = self._get_tariffs()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Tariff Report')

        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1})
        cell_fmt = workbook.add_format({'border': 1})
        money_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})

        headers = [
            'GD No.', 'GD Date', 'Vendor', 'Item', 'HS Code', 'Qty', 'UOM',
            'Assessed Unit Value', 'Assessed Total Value',
            'Assessed Unit Value (PKR)', 'Assessed Total Value (PKR)',
            'CD %', 'CD (PKR)', 'RD %', 'RD (PKR)', 'ACD %', 'ACD (PKR)',
            'ST %', 'ST (PKR)', 'AST %', 'AST (PKR)', 'IT %', 'IT (PKR)',
            'Total Sum Payable (PKR)',
        ]
        for col, title in enumerate(headers):
            sheet.write(0, col, title, header_fmt)
            sheet.set_column(col, col, 18)

        row = 1
        for tariff in tariffs:
            for line in tariff.line_ids:
                text_values = [
                    tariff.dg_no,
                    str(tariff.gd_date or ''),
                    tariff.partner_id.name or '',
                    line.product_id.display_name or '',
                    line.hs_code_id.code or '',
                    line.qty,
                    line.uom_id.name or '',
                ]
                for col, val in enumerate(text_values):
                    sheet.write(row, col, val, cell_fmt)

                money_values = [
                    line.assessed_unit_value, line.assessed_total_value,
                    line.assessed_unit_value_pkr, line.assessed_total_value_pkr,
                    line.cd_percentage, line.cd_pkr,
                    line.rd_percentage, line.rd_pkr,
                    line.acd_percentage, line.acd_pkr,
                    line.st_percentage, line.st_pkr,
                    line.ast_percentage, line.ast_pkr,
                    line.it_percentage, line.it_pkr,
                    line.total_payable_pkr,
                ]
                for i, val in enumerate(money_values):
                    sheet.write(row, len(text_values) + i, val, money_fmt)
                row += 1

        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': 'Tariff_Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
