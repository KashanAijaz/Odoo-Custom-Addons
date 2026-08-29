# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TariffReportXlsx(models.AbstractModel):
    _name = 'report.tdc_import.tariff_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Tariff Excel Report'

    def generate_xlsx_report(self, workbook, data, docs):
        # Create styles
        header_style = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#4472C4',
            'font_color': '#FFFFFF',
            'border': 1,
            'font_size': 10,
            'text_wrap': True
        })
        
        title_style = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 16,
            'fg_color': '#D9E2F3',
            'border': 1
        })
        
        normal_style = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 9
        })
        
        number_style = workbook.add_format({
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0.00',
            'font_size': 9
        })
        
        total_style = workbook.add_format({
            'bold': True,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0.00',
            'fg_color': '#E2EFDA',
            'font_size': 9
        })
        
        summary_style = workbook.add_format({
            'bold': True,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0.00',
            'fg_color': '#FFF2CC',
            'font_size': 11
        })

        for doc in docs:
            # Create sheet with reference name
            sheet_name = doc.reference or 'Tariff Report'
            sheet = workbook.add_worksheet(sheet_name[:31])  # Excel sheet name max 31 chars
            
            # Set column widths
            sheet.set_column('A:A', 5)    # #
            sheet.set_column('B:B', 20)   # Description
            sheet.set_column('C:C', 12)   # HS Code
            sheet.set_column('D:D', 8)    # Qty
            sheet.set_column('E:E', 10)   # UOM
            sheet.set_column('F:F', 18)   # Assessed Unit Value EUR
            sheet.set_column('G:G', 18)   # Assessed Total Value EUR
            sheet.set_column('H:H', 18)   # Assessed Unit Value PKR
            sheet.set_column('I:I', 18)   # Assessed Total Value PKR
            sheet.set_column('J:J', 8)    # CD %
            sheet.set_column('K:K', 15)   # CD PKR
            sheet.set_column('L:L', 8)    # RD %
            sheet.set_column('M:M', 15)   # RD PKR
            sheet.set_column('N:N', 8)    # ACD %
            sheet.set_column('O:O', 15)   # ACD PKR
            sheet.set_column('P:P', 8)    # ST %
            sheet.set_column('Q:Q', 15)   # ST PKR
            sheet.set_column('R:R', 8)    # AST %
            sheet.set_column('S:S', 15)   # AST PKR
            sheet.set_column('T:T', 8)    # IT %
            sheet.set_column('U:U', 15)   # IT PKR
            sheet.set_column('V:V', 18)   # Total Payable PKR

            row = 0
            
            # Title
            sheet.merge_range(row, 0, row, 21, f'TARIFF IMPORT REPORT - {doc.reference}', title_style)
            row += 2
            
            # Header Information
            header_data = [
                ['Reference:', doc.reference or ''],
                ['DG Number:', doc.dg_no or ''],
                ['GD Date:', fields.Date.to_string(doc.gd_date) if doc.gd_date else ''],
                ['Vendor:', doc.vendor_id.display_name or ''],
                ['Currency:', doc.currency_id.display_name or ''],
                ['Exchange Rate:', str(doc.exchange_rate)],
                ['Insurance %:', f'{doc.insurance_percent}%'],
                ['Landing Charges %:', f'{doc.landing_charges_percent}%'],
            ]
            
            for label, value in header_data:
                sheet.merge_range(row, 0, row, 3, label, normal_style)
                sheet.merge_range(row, 4, row, 10, value, normal_style)
                row += 1
            
            row += 1

            # Table Headers
            headers = [
                '#', 'Description', 'HS Code', 'Qty', 'UOM',
                'Assessed Unit Value (EUR)', 'Assessed Total Value (EUR)',
                'Assessed Unit Value (PKR)', 'Assessed Total Value (PKR)',
                'CD %', 'CD (PKR)', 'RD %', 'RD (PKR)',
                'ACD %', 'ACD (PKR)', 'ST %', 'ST (PKR)',
                'AST %', 'AST (PKR)', 'IT %', 'IT (PKR)',
                'Total Payable (PKR)'
            ]
            
            for col, header in enumerate(headers):
                sheet.write(row, col, header, header_style)
            row += 1

            # Table Data
            total_cd = total_rd = total_acd = total_st = total_ast = total_it = total_payable = 0
            line_index = 1
            
            for line in doc.line_ids:
                sheet.write(row, 0, line_index, number_style)
                sheet.write(row, 1, line.description or '', normal_style)
                sheet.write(row, 2, line.hs_code or '', normal_style)
                sheet.write(row, 3, line.quantity, number_style)
                sheet.write(row, 4, line.uom_id.display_name or '', normal_style)
                sheet.write(row, 5, line.assessed_unit_value_eur, number_style)
                sheet.write(row, 6, line.assessed_total_value_eur, number_style)
                sheet.write(row, 7, line.assessed_unit_value_pkr, number_style)
                sheet.write(row, 8, line.assessed_total_value_pkr, number_style)
                sheet.write(row, 9, line.cd_percentage, number_style)
                sheet.write(row, 10, line.cd_pkr, number_style)
                sheet.write(row, 11, line.rd_percentage, number_style)
                sheet.write(row, 12, line.rd_pkr, number_style)
                sheet.write(row, 13, line.acd_percentage, number_style)
                sheet.write(row, 14, line.acd_pkr, number_style)
                sheet.write(row, 15, line.st_percentage, number_style)
                sheet.write(row, 16, line.st_pkr, number_style)
                sheet.write(row, 17, line.ast_percentage, number_style)
                sheet.write(row, 18, line.ast_pkr, number_style)
                sheet.write(row, 19, line.it_percentage, number_style)
                sheet.write(row, 20, line.it_pkr, number_style)
                sheet.write(row, 21, line.total_payable_pkr, number_style)
                
                total_cd += line.cd_pkr
                total_rd += line.rd_pkr
                total_acd += line.acd_pkr
                total_st += line.st_pkr
                total_ast += line.ast_pkr
                total_it += line.it_pkr
                total_payable += line.total_payable_pkr
                line_index += 1
                row += 1

            # Total Row
            sheet.write(row, 0, 'TOTAL', total_style)
            sheet.write(row, 8, doc.total_assessed_value_pkr, total_style)
            sheet.write(row, 10, total_cd, total_style)
            sheet.write(row, 12, total_rd, total_style)
            sheet.write(row, 14, total_acd, total_style)
            sheet.write(row, 16, total_st, total_style)
            sheet.write(row, 18, total_ast, total_style)
            sheet.write(row, 20, total_it, total_style)
            sheet.write(row, 21, total_payable, total_style)
            row += 2

            # Summary Section
            sheet.merge_range(row, 0, row, 21, 'SUMMARY', title_style)
            row += 1
            
            summary_data = [
                ['Total Assessed Value (EUR):', doc.total_assessed_value_eur],
                ['Total Assessed Value (PKR):', doc.total_assessed_value_pkr],
                ['Total CD (PKR):', doc.total_cd_pkr],
                ['Total RD (PKR):', doc.total_rd_pkr],
                ['Total ACD (PKR):', doc.total_acd_pkr],
                ['Total ST (PKR):', doc.total_st_pkr],
                ['Total AST (PKR):', doc.total_ast_pkr],
                ['Total IT (PKR):', doc.total_it_pkr],
                ['GRAND TOTAL PAYABLE (PKR):', doc.total_sum_payable_pkr],
            ]
            
            for label, value in summary_data:
                sheet.write(row, 0, label, normal_style)
                sheet.write(row, 1, value, summary_style if 'GRAND' in label else number_style)
                row += 1

        return workbook