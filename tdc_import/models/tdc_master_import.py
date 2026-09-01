# -*- coding: utf-8 -*-
from odoo import models, fields, api
from math import floor
import io
import base64
import xlsxwriter

def _round_half_up(value):
    """Round to the nearest whole number, half-up (e.g. 79.35 -> 79, 79.50 -> 80)."""
    if not value:
        return 0.0
    integer = floor(value)
    decimal = round((value - integer) * 100)
    if decimal >= 50:
        integer += 1
    return float(integer)

def _round_to_nearest_10(value):
    """Round to the nearest multiple of 10, half-up (e.g. 244 -> 240, 245 -> 250)."""
    if not value:
        return 0.0
    scaled = value / 10.0
    integer = floor(scaled)
    decimal = round((scaled - integer) * 100)
    if decimal >= 50:
        integer += 1
    return float(integer) * 10.0

def _build_copy_vals(record, exclude=()):
    """Build a vals dict of every plain, user-enterable field on `record`
    (skips computed/related fields and one2many/many2many), ready to use
    in a create/write call."""
    vals = {}
    for fname, rfield in record._fields.items():
        if rfield.compute or rfield.related or rfield.type in ('one2many', 'many2many'):
            continue
        if fname in ('id', 'display_name', 'create_date', 'create_uid', 'write_date', 'write_uid'):
            continue
        if fname in exclude:
            continue
        value = record[fname]
        vals[fname] = value.id if rfield.type == 'many2one' else value
    return vals

PARTY_FIELDS = [
    ('Consignee Name', lambda o: o.consignee_id),
    ('Notify/3rd Party Name', lambda o: o.notify_party_id.name if o.notify_party_id else ''),
    ('Mode of Transport', lambda o: dict(o._fields['mode_of_transport'].selection).get(o.mode_of_transport, '')),
    ('Clearing Agent Name', lambda o: o.clearing_agent_id.name if o.clearing_agent_id else ''),
    ('Freight Forwarder Name', lambda o: o.freight_forwarder_id.name if o.freight_forwarder_id else ''),
    ('Godown Name', lambda o: o.godown_id.name if o.godown_id else ''),
    ('Ocean Vessel/Flight Name', lambda o: o.vessel_id.name if o.vessel_id else ''),
    ('Consignment Type', lambda o: (o.consignment_type or '').upper()),
    ('IGM Collectorate/Terminal', lambda o: o.igm_terminal_id.name if o.igm_terminal_id else ''),
    ('Customs Collectorate', lambda o: o.customs_collectorate_id.name if o.customs_collectorate_id else ''),
    ('House HBL/HAWB No.', lambda o: o.house_bl_no),
    ('Bank Involved', lambda o: (o.bank_involved or '').capitalize()),
    ('Financial Instrument No.', lambda o: o.financial_instrument_no),
    ('Financial Instrument Value', lambda o: o.financial_instrument_value),
    ('Consignee Bank Name', lambda o: o.consignee_bank_name),
    ('Consignee Bank Branch', lambda o: o.consignee_bank_branch),
]

LINE_FIELDS = [
    ('Item', lambda l: l.product_id.name if l.product_id else ''),
    ('HS Code', lambda l: l.hs_code_id.code if l.hs_code_id else ''),
    ('Qty', lambda l: l.qty),
    ('UOM', lambda l: l.uom_id.name if l.uom_id else ''),
    ('Unit Rate Actual (USD)', lambda l: l.unit_rate_actual_usd),
    ('Total Amount Actual (USD)', lambda l: l.total_amount_actual_usd),
    ('Bank Charges at Origin (USD)', lambda l: l.bank_charges_origin_usd),
    ('Packing Charges at Origin (USD)', lambda l: l.packing_charges_origin_usd),
    ('Total EXW Price at Origin (PKR)', lambda l: l.total_exw_price_origin_pkr),
    ('Value % Share', lambda l: l.value_pct_share),
    ('Unit Chargeable Weight CW (Kg)', lambda l: l.unit_cw_kg),
    ('Total Chargeable Weight CW (Kg)', lambda l: l.total_cw_kg),
    ('Weight % Share - Total', lambda l: l.weight_pct_share),
    ('Sea Freight TOTAL (USD)', lambda l: l.sea_freight_total_usd),
    ('Sea Freight PER UNIT (USD)', lambda l: l.sea_freight_per_unit_usd),
    ('Sea Freight for TOTAL (PKR)', lambda l: l.sea_freight_total_pkr),
    ('TOTAL C&F KARACHI COST', lambda l: l.total_cf_karachi_cost),
    ('Freight Expense from Origin to UAE', lambda l: l.freight_expense_origin_uae),
    ('UAE Customs Clearance Expense', lambda l: l.uae_customs_clearance_expense),
    ('VAT Paid at Customs Clearance (UAE)', lambda l: l.uae_vat_paid_customs_clearance),
    ('UAE Bank Expenses', lambda l: l.uae_bank_expenses),
    ('UAE Company Expenses', lambda l: l.uae_company_expenses),
    ('UAE Courier Charges', lambda l: l.uae_courier_charges),
    ('Any Other UAE Expense', lambda l: l.uae_any_other_expense),
    ('TOTAL UAE EXPENSES', lambda l: l.total_uae_expenses),
    ('PC CESS Sindh Excise Duty', lambda l: l.pc_cess_sindh_excise_duty),
    ('PC Sindh Stamp Duty', lambda l: l.pc_sindh_stamp_duty),
    ('PC PSW GD Fee', lambda l: l.pc_psw_gd_fee),
    ('PC Invoice Not Found Penalty', lambda l: l.pc_invoice_not_found_penalty),
    ('PC Any Other Charges', lambda l: l.pc_any_other_charges),
    ('Customs Duty (CD+RD+ACD)', lambda l: l.customs_duty_line),
    ('Sales Tax (ST+AST)', lambda l: l.sales_tax_line),
    ('Income Tax (IT)', lambda l: l.income_tax_line),
    ('TOTAL Duty Taxes', lambda l: l.total_duty_tax_line),
    ('Godown/Shed Charge', lambda l: l.dest_godown_shed_charges),
    ('Delivery Order DO Charges', lambda l: l.dest_delivery_order_charges),
    ('PSW Token for GD Submission', lambda l: l.dest_psw_token_gd_submission),
    ('Civil Aviation CAA Charges', lambda l: l.dest_caa_charges),
    ('Transport Port/Airport to Warehouse', lambda l: l.dest_transport_port_warehouse),
    ('Clearing Agent Fees', lambda l: l.dest_clearing_agent_fees),
    ('MISC. Examination Expense', lambda l: l.dest_misc_examination_expense),
    ('MISC. Assessment Expense', lambda l: l.dest_misc_assessment_expense),
    ('MISC. Delivery/Gateout Expense', lambda l: l.dest_misc_delivery_gateout_expense),
    ('Any Other Expense - Transport/Bykea', lambda l: l.dest_any_other_expense_transport),
    ('TOTAL CUSTOMS CLEARANCE (Excl. ST)', lambda l: l.total_customs_clearance_cost_excl_st),
    ('TOTAL CUSTOMS CLEARANCE (Incl. ST)', lambda l: l.total_customs_clearance_cost_incl_st),
    ('UNIT HOME COST (Excl. GST)', lambda l: l.total_home_cost_excl_gst),
    ('TOTAL HOME COST (Incl. GST)', lambda l: l.total_home_cost_incl_gst),
    ('UNIT HOME Cost (Incl. GST)', lambda l: l.unit_home_cost_incl_gst),
]

PCT_LABELS = {'Value % Share', 'Weight % Share - Total'}

class TdcMasterImport(models.Model):
    _name = 'tdc.master.import'
    _description = 'Import Master (GD Costing)'
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(string='Reference', default='New', copy=False, readonly=True)

    # ------------------------------------------------------------------
    # Link to the GD Tariff — selecting this pulls in product/HS lines
    # and the customs duty/tax totals below.
    # ------------------------------------------------------------------
    tariff_id = fields.Many2one(
        'tdc.import.tariff', string='GD No.', required=True,
        help='Select the GD Tariff record. Product/HS-code lines and duty & tax '
             'totals are pulled from it automatically.'
    )
    gd_date = fields.Date(related='tariff_id.gd_date', string='GD Date', store=True, readonly=True)
    partner_id = fields.Many2one(related='tariff_id.partner_id', string='Vendor', store=True, readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company
    )

    # ------------------------------------------------------------------
    # "Product detail and pricing as per origin" — auto-populated from
    # the selected GD Tariff's lines when tariff_id is picked, then
    # extended here with origin-costing fields (unit rate USD, EXW
    # price, % share) that don't belong on the base GD Tariff.
    # ------------------------------------------------------------------
    product_line_ids = fields.One2many(
        'tdc.master.import.product.line', 'master_id',
        string='Product Detail and Pricing as per Origin',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'charge_line_ids' in fields_list:
            charge_products = self.env['product.product'].search([
                ('categ_id', '=', self.env.ref('tdc_import.product_category_tdc_import_charges').id),
                ('type', '=', 'service'),
            ])
            res['charge_line_ids'] = [
                (0, 0, {'product_id': p.id, 'amount': 0.0})
                for p in charge_products
            ]
        return res

    @api.onchange('tariff_id')
    def _onchange_tariff_id(self):
        for rec in self:
            if not rec.tariff_id:
                rec.product_line_ids = [(5, 0, 0)]
                continue

            existing = self.env['tdc.master.import'].search([
                ('tariff_id', '=', rec.tariff_id.id),
                ('id', '!=', rec._origin.id),
            ], order='id desc', limit=1)

            if existing:
                # Pull EVERY field from the most recent document saved
                # against this same GD — header fields, every product
                # line, every charge line, in full.
                header_vals = _build_copy_vals(existing, exclude=('tariff_id', 'name'))
                for fname, value in header_vals.items():
                    rec[fname] = value

                line_commands = [(5, 0, 0)]
                for src_line in existing.product_line_ids:
                    line_commands.append((0, 0, _build_copy_vals(src_line, exclude=('master_id',))))
                rec.product_line_ids = line_commands

                charge_commands = [(5, 0, 0)]
                for cl in existing.charge_line_ids:
                    charge_commands.append((0, 0, _build_copy_vals(cl, exclude=('master_id',))))
                rec.charge_line_ids = charge_commands
                continue

            # No prior document for this GD — pull base product/HS/qty/uom
            # straight from the GD Tariff lines.
            line_commands = [(5, 0, 0)]
            for tl in rec.tariff_id.line_ids:
                line_commands.append((0, 0, {
                    'tariff_line_id': tl.id,
                    'product_id': tl.product_id.id,
                    'hs_code_id': tl.hs_code_id.id,
                    'qty': tl.qty,
                    'uom_id': tl.uom_id.id,
                    'unit_rate_actual_usd' : tl.price_unit

                }))
            rec.product_line_ids = line_commands
    # ------------------------------------------------------------------
    # "PAKISTAN CUSTOMS - DUTY & TAXES AS PER GD"
    # ------------------------------------------------------------------
    customs_duty_total = fields.Float(
        string='Customs Duty (CD+RD+ACD)', compute='_compute_duty_tax_summary', store=True
    )
    sales_tax_total = fields.Float(
        string='Sales Tax (ST+AST)', compute='_compute_duty_tax_summary', store=True
    )
    income_tax_total = fields.Float(
        string='Income Tax (IT)', compute='_compute_duty_tax_summary', store=True
    )
    total_duty_tax = fields.Float(
        string='Total Duty & Taxes', compute='_compute_duty_tax_summary', store=True
    )

    @api.depends(
        'tariff_id.amount_cd_total', 'tariff_id.amount_rd_total', 'tariff_id.amount_acd_total',
        'tariff_id.amount_st_total', 'tariff_id.amount_ast_total', 'tariff_id.amount_it_total',
        'tariff_id.amount_total_payable',
    )
    def _compute_duty_tax_summary(self):
        for rec in self:
            t = rec.tariff_id
            rec.customs_duty_total = (t.amount_cd_total + t.amount_rd_total + t.amount_acd_total) if t else 0.0
            rec.sales_tax_total = (t.amount_st_total + t.amount_ast_total) if t else 0.0
            rec.income_tax_total = t.amount_it_total if t else 0.0
            rec.total_duty_tax = t.amount_total_payable if t else 0.0

    # ------------------------------------------------------------------
    # Origin payment / freight exchange rates (as supplied)
    # ------------------------------------------------------------------
    origin_payment_exchange_rate_usd = fields.Float(string='Origin Payment Exch. Rt. USD')
    freight_exch_rate_usd = fields.Float(
        string='Freight Exch. Rt. USD', digits=(16, 4),
        help='Used to convert the origin EXW price into PKR on each product line.'
    )

    # ------------------------------------------------------------------
    # Consignee / shipment details
    # ------------------------------------------------------------------
    consignee_id = fields.Many2one(
        'res.partner',
        string='Consignee',
        domain="[('x_vendor_type', 'in', ['welkin', 'athar'])]",
    )
    notify_party_id = fields.Many2one('res.partner', string='Notify/3rd Party Name')
    mode_of_transport = fields.Selection(
        [('sea', 'Sea'), ('air', 'By Air'), ('land', 'By Land')],
        string='Mode of Transport'
    )
    clearing_agent_id = fields.Many2one('res.partner', string='Clearing Agent Name')
    freight_forwarder_id = fields.Many2one('res.partner', string='Freight Forwarder Name')
    godown_id = fields.Many2one('res.partner', string='Godown Name')

    port_of_loading_id = fields.Many2one('tdc.port', string='Port of Loading (POL)')
    port_of_discharge_id = fields.Many2one('tdc.port', string='Port of Discharge (POD)')
    vessel_id = fields.Many2one('tdc.vessel', string='Ocean Vessel/Flight Name')
    consignment_type = fields.Selection(
        [('lcl', 'LCL'), ('fcl', 'FCL')], string='Consignment Type'
    )
    igm_terminal_id = fields.Many2one('tdc.igm.terminal', string='IGM Collectorate/Terminal')
    customs_collectorate_id = fields.Many2one('tdc.customs.collectorate', string='Customs Collectorate')

    master_bl_no = fields.Char(string='Master BL/MAWB No.')
    house_bl_no = fields.Char(string='House HBL/HAWB No.')

    # ------------------------------------------------------------------
    # Banking details
    # ------------------------------------------------------------------
    bank_involved = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string='Bank Involved', default='no'
    )
    financial_instrument_no = fields.Char(string='Financial Instrument No.')
    financial_instrument_value = fields.Char(string='Financial Instrument Value')
    consignee_bank_name = fields.Char(string='Consignee Bank Name')
    consignee_bank_branch = fields.Char(string='Consignee Bank Branch')

    # ------------------------------------------------------------------
    # Local/other charges (service products, amount entered manually)
    # ------------------------------------------------------------------
    charge_line_ids = fields.One2many(
        'tdc.master.import.charge.line', 'master_id', string='Local & Other Charges'
    )
    total_charges = fields.Float(
        string='Total Charges', compute='_compute_total_charges', store=True
    )

    @api.depends('charge_line_ids.amount')
    def _compute_total_charges(self):
        for rec in self:
            rec.total_charges = sum(rec.charge_line_ids.mapped('amount'))

    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('tdc.master.import') or 'New'
        return super().create(vals_list)
    
    def action_download_excel(self):
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        navy, light_navy, grey = '#1F3864', '#D9E2F3', '#D9D9D9'
        f_title = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': navy,
                                        'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
        f_label = workbook.add_format({'bold': True, 'font_color': '#404040'})
        f_value = workbook.add_format({'border': 1})
        f_colhdr = workbook.add_format({'bold': True, 'bg_color': light_navy, 'font_color': navy,
                                         'border': 1, 'align': 'center', 'valign': 'vcenter',
                                         'text_wrap': True})
        f_money = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        f_pct = workbook.add_format({'border': 1, 'num_format': '0.00%'})
        f_text = workbook.add_format({'border': 1})
        f_total = workbook.add_format({'bold': True, 'bg_color': grey, 'border': 1, 'num_format': '#,##0.00'})

        # ---------------- Sheet 1: header + item-wise table ----------------
        ws1 = workbook.add_worksheet('Import Master Costing')
        ws1.merge_range(0, 0, 0, len(LINE_FIELDS), 'IMPORT MASTER — GD COSTING SHEET', f_title)

        header_pairs = [
            ('Company Name', self.partner_id.name if self.partner_id else ''),
            ('GD No.', self.tariff_id.dg_no if self.tariff_id else ''),
            ('GD Date', str(self.gd_date or '')),
            ('B/L No.', self.master_bl_no or ''),
            ('Port of Loading', self.port_of_loading_id.name if self.port_of_loading_id else ''),
            ('Port of Discharge', self.port_of_discharge_id.name if self.port_of_discharge_id else ''),
            ('Origin Payment Exch. Rt. USD', self.origin_payment_exchange_rate_usd or 0.0),
            ('Freight Exch. Rt. USD', self.freight_exch_rate_usd or 0.0),
        ]
        row = 2
        for i in range(0, len(header_pairs), 2):
            for j, (label, value) in enumerate(header_pairs[i:i + 2]):
                col = j * 4
                ws1.write(row, col, label, f_label)
                ws1.write(row, col + 1, value, f_value)
            row += 1

        row += 1
        for i, (label, _getter) in enumerate(LINE_FIELDS):
            ws1.write(row, i, label, f_colhdr)
        ws1.set_row(row, 32)

        data_start = row + 1
        for r, line in enumerate(self.product_line_ids, start=data_start):
            for c, (label, getter) in enumerate(LINE_FIELDS):
                raw = getter(line)
                if isinstance(raw, str):
                    ws1.write(r, c, raw, f_text)
                else:
                    value = raw or 0
                    fmt = f_pct if label in PCT_LABELS else f_money
                    ws1.write(r, c, value, fmt)

        total_row = data_start + len(self.product_line_ids)
        ws1.write(total_row, 0, 'TOTAL', f_total)
        skip = {'Item', 'HS Code', 'UOM', 'Unit Rate Actual (USD)', 'Value % Share',
                'Unit Chargeable Weight CW (Kg)', 'Weight % Share - Total',
                'Sea Freight PER UNIT (USD)', 'UNIT HOME Cost (Incl. GST)'}
        for c, (label, _getter) in enumerate(LINE_FIELDS):
            if label in skip:
                ws1.write(total_row, c, '', f_total)
                continue
            col_letter = xlsxwriter.utility.xl_col_to_name(c)
            ws1.write_formula(
                total_row, c,
                f'=SUM({col_letter}{data_start + 1}:{col_letter}{total_row})',
                f_total,
            )
        for c in range(len(LINE_FIELDS)):
            ws1.set_column(c, c, 16)

        # ---------------- Sheet 2: shipment/consignee + charges ----------------
        ws2 = workbook.add_worksheet('Shipment & Charges Details')
        ws2.merge_range(0, 0, 0, 4, 'SHIPMENT, CONSIGNEE & LOCAL CHARGES DETAIL', f_title)
        ws2.set_column(0, 0, 30)
        ws2.set_column(1, 1, 30)

        row = 2
        for label, getter in PARTY_FIELDS:
            ws2.write(row, 0, label, f_label)
            ws2.write(row, 1, getter(self) or '', f_value)
            row += 1

        row += 1
        ws2.write(row, 0, 'Charge / Service Product', f_colhdr)
        ws2.write(row, 1, 'Amount', f_colhdr)
        charges_start = row + 1
        for r, charge in enumerate(self.charge_line_ids, start=charges_start):
            ws2.write(r, 0, charge.product_id.name if charge.product_id else '', f_text)
            ws2.write(r, 1, charge.amount or 0.0, f_money)

        charges_end = charges_start + len(self.charge_line_ids) - 1
        total_r = charges_start + len(self.charge_line_ids)
        ws2.write(total_r, 0, 'TOTAL CHARGES', f_total)
        if charges_end >= charges_start:
            ws2.write_formula(total_r, 1, f'=SUM(B{charges_start + 1}:B{charges_end + 1})', f_total)
        else:
            ws2.write(total_r, 1, 0, f_total)

        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': f'{self.name or "Import_Master"}.xlsx',
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


class TdcMasterImportChargeLine(models.Model):
    _name = 'tdc.master.import.charge.line'
    _description = 'Import Master - Local/Other Charge Line'
    _order = 'id'

    master_id = fields.Many2one(
        'tdc.master.import', string='Import Master', required=True, ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product', string='Charge', required=True,
        domain=[('type', '=', 'service')],
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    amount = fields.Monetary(string='Amount', currency_field='currency_id')


class TdcMasterImportProductLine(models.Model):
    _name = 'tdc.master.import.product.line'
    _description = 'Import Master - Product Detail and Pricing as per Origin'
    _order = 'sequence, id'

    master_id = fields.Many2one(
        'tdc.master.import', string='Import Master', required=True, ondelete='cascade'
    )
    sequence = fields.Integer(default=10)

    # -- copied in automatically from the GD Tariff line on tariff_id change --
    product_id = fields.Many2one('product.product', string='Item')
    hs_code_id = fields.Many2one('hs.code', string='HS Code')
    qty = fields.Float(string='Qty')
    uom_id = fields.Many2one('uom.uom', string='UOM')

    # -- origin pricing (user entered / computed) --
    unit_rate_actual_usd = fields.Float(
        string='Unit Rate Actual (USD)', digits=(16, 4)
    )
    total_amount_actual_usd = fields.Float(
        string='Total Amount Actual (USD)', compute='_compute_total_amount_actual_usd', store=True,
        help='Unit Rate Actual (USD) * Qty'
    )
    bank_charges_origin_usd = fields.Float(
        string='Bank Charges at Origin (USD)', compute='_compute_origin_charges', store=True,
        help="Total 'Bank Charges' entered under Local & Other Charges, apportioned by this "
             "line's Value % Share."
    )
    packing_charges_origin_usd = fields.Float(
        string='Packing Charges at Origin (USD)', compute='_compute_origin_charges', store=True,
        help="Total 'Packing Charges at Origin' entered under Local & Other Charges, "
             "apportioned by this line's Value % Share."
    )
    total_exw_price_origin_pkr = fields.Float(
        string='Total EXW Price at Origin (PKR)', compute='_compute_total_exw_price_origin_pkr', store=True,
        help='(Total Amount Actual (USD) + Bank Charges at Origin (USD) + Packing Charges '
             'at Origin (USD)) * Freight Exch. Rt. USD'
    )

    # -- % Share Detail --
    value_pct_share = fields.Float(
        string='Value % Share (on Total Qty)', compute='_compute_value_pct_share', store=True,
        help='This line\'s Total Amount Actual (USD) / sum of Total Amount Actual (USD) '
             'across all lines on this document.'
    )
    unit_cw_kg = fields.Float(
        string='Unit Chargeable Weight CW (Kg)',
        compute='_compute_unit_cw_kg', store=True, readonly=False, precompute=True,
        help='Auto-filled from the product\'s Chargeable Weight (TDC Customization tab). '
            'Editable — can be overridden manually per line.'
    )
    total_cw_kg = fields.Float(
        string='Total Chargeable Weight CW (Kg)', compute='_compute_total_cw_kg', store=True,
        help='Unit Chargeable Weight CW (Kg) * Qty'
    )
    weight_pct_share = fields.Float(
        string='Weight % Share - Total', compute='_compute_weight_pct_share', store=True,
        help='This line\'s Total Chargeable Weight CW (Kg) / sum of Total Chargeable Weight '
             'CW (Kg) across all lines on this document.'
    )

    @api.depends('unit_rate_actual_usd', 'qty')
    def _compute_total_amount_actual_usd(self):
        for line in self:
            line.total_amount_actual_usd = (line.unit_rate_actual_usd or 0.0) * (line.qty or 0.0)

    @api.depends('total_amount_actual_usd', 'master_id.product_line_ids.total_amount_actual_usd')
    def _compute_value_pct_share(self):
        for line in self:
            total = sum(line.master_id.product_line_ids.mapped('total_amount_actual_usd'))
            line.value_pct_share = (line.total_amount_actual_usd / total) if total else 0.0
#############################################################
    @api.depends('product_id')
    def _compute_unit_cw_kg(self):
        for line in self:
            line.unit_cw_kg = line.product_id.cw_weight if line.product_id else 0.0

    #########################################
    @api.depends('unit_cw_kg', 'qty')
    def _compute_total_cw_kg(self):
        for line in self:
            line.total_cw_kg = (line.unit_cw_kg or 0.0) * (line.qty or 0.0)

    @api.depends('total_cw_kg', 'master_id.product_line_ids.total_cw_kg')
    def _compute_weight_pct_share(self):
        for line in self:
            total = sum(line.master_id.product_line_ids.mapped('total_cw_kg'))
            line.weight_pct_share = (line.total_cw_kg / total) if total else 0.0

    @api.depends(
        'value_pct_share',
        'master_id.charge_line_ids.amount', 'master_id.charge_line_ids.product_id',
    )
    def _compute_origin_charges(self):
        for line in self:
            charges = line.master_id.charge_line_ids
            bank_total = sum(
                charges.filtered(lambda c: c.product_id.name == 'Bank Charges At Origin (USD)').mapped('amount')
            )
            packing_total = sum(
                charges.filtered(lambda c: c.product_id.name == 'Packing Charges at Origin').mapped('amount')
            )
            line.bank_charges_origin_usd = bank_total * line.value_pct_share
            line.packing_charges_origin_usd = packing_total * line.value_pct_share

    @api.depends(
        'total_amount_actual_usd', 'bank_charges_origin_usd', 'packing_charges_origin_usd',
        'master_id.freight_exch_rate_usd',
    )
    def _compute_total_exw_price_origin_pkr(self):
        for line in self:
            rate = line.master_id.freight_exch_rate_usd or 0.0
            line.total_exw_price_origin_pkr = (
                line.total_amount_actual_usd
                + line.bank_charges_origin_usd
                + line.packing_charges_origin_usd
            ) * rate
    # -- Freight & Handling Charges --
    sea_freight_total_usd = fields.Float(
        string='Sea Freight TOTAL (USD)', compute='_compute_sea_freight_total_usd', store=True,
        help="'Sea/Air/Land Freight (Grand Total)' entered under Local & Other Charges, "
             "apportioned by this line's Weight % Share - Total."
    )
    sea_freight_per_unit_usd = fields.Float(
        string='Sea Freight PER UNIT (USD)', compute='_compute_sea_freight_per_unit_usd', store=True,
        help='Sea Freight TOTAL (USD) / Qty'
    )
    sea_freight_total_pkr = fields.Float(
        string='Sea Freight for TOTAL (PKR)', compute='_compute_sea_freight_total_pkr', store=True,
        help='Sea Freight TOTAL (USD) * Freight Exch. Rt. USD'
    )
    total_cf_karachi_cost = fields.Float(
        string='TOTAL C&F KARACHI COST', compute='_compute_total_cf_karachi_cost', store=True,
        help='Sea Freight for TOTAL (PKR) + Total EXW Price at Origin (PKR)'
    )

    @api.depends(
        'weight_pct_share',
        'master_id.charge_line_ids.amount', 'master_id.charge_line_ids.product_id',
    )
  
    @api.depends(
        'weight_pct_share',
        'master_id.charge_line_ids.amount', 'master_id.charge_line_ids.product_id',
    )
    def _compute_sea_freight_total_usd(self):
        for line in self:
            charges = line.master_id.charge_line_ids
            freight_total = sum(
                charges.filtered(
                    lambda c: c.product_id.name == 'Sea/Air/Land Freight (Grand Total)'
                ).mapped('amount')
            )
            line.sea_freight_total_usd = (freight_total * line.weight_pct_share) #_round_half_up
    @api.depends('sea_freight_total_usd', 'qty')
    def _compute_sea_freight_per_unit_usd(self):
        for line in self:
            line.sea_freight_per_unit_usd = (
                line.sea_freight_total_usd / line.qty
            ) if line.qty else 0.0

    @api.depends('sea_freight_total_usd', 'master_id.freight_exch_rate_usd')
    def _compute_sea_freight_total_pkr(self):
        for line in self:
            rate = line.master_id.freight_exch_rate_usd or 0.0
            line.sea_freight_total_pkr = line.sea_freight_total_usd * rate

    @api.depends('sea_freight_total_pkr', 'total_exw_price_origin_pkr')
    def _compute_total_cf_karachi_cost(self):
        for line in self:
            line.total_cf_karachi_cost = line.sea_freight_total_pkr + line.total_exw_price_origin_pkr
    
    # -- Third Party UAE Shipment Expense --
    freight_expense_origin_uae = fields.Float(string='Freight Expense from Origin to UAE',compute='_compute_uae_apportioned_expenses')
    uae_customs_clearance_expense = fields.Float(
        string='UAE Customs Clearance Expense (Excl. VAT Paid)',
        compute='_compute_uae_apportioned_expenses'
    )
    uae_vat_paid_customs_clearance = fields.Float(string='VAT Paid at Customs Clearance (UAE)',compute='_compute_uae_apportioned_expenses')
    uae_bank_expenses = fields.Float(
        string='UAE Bank Expenses', compute='_compute_uae_apportioned_expenses', store=True,
        help="'Total UAE Bank Expenses' entered under Local & Other Charges, apportioned "
             "by this line's Value % Share."
    )
    uae_company_expenses = fields.Float(
        string='UAE Company Expenses', compute='_compute_uae_apportioned_expenses', store=True,
        help="'Total UAE Company Expenses' entered under Local & Other Charges, apportioned "
             "by this line's Value % Share."
    )
    uae_courier_charges = fields.Float(
        string='DHL/TCS/Fedex etc. Docs Courier Charges to UAE Bank',
        compute='_compute_uae_apportioned_expenses', store=True,
        help="'TDHL/TCS/Fedex etc. Docs Courier Charges to UAE Bank' entered under Local & "
             "Other Charges, apportioned by this line's Value % Share."
    )
    uae_any_other_expense = fields.Float(string='Any Other UAE Expense')
    total_uae_expenses = fields.Float(
        string='TOTAL UAE EXPENSES', compute='_compute_total_uae_expenses', store=True,
        help='Sum of all Third Party UAE Shipment Expense fields.'
    )

    @api.depends(
        'value_pct_share',
        'master_id.charge_line_ids.amount', 'master_id.charge_line_ids.product_id',
    )
    def _compute_uae_apportioned_expenses(self):
        for line in self:
            charges = line.master_id.charge_line_ids
            freight_total = sum(
            charges.filtered(lambda c: c.product_id.name == 'Freight Expense from Origin to UAE').mapped('amount')
            )
            customs_clearance_total = sum(
                charges.filtered(lambda c: c.product_id.name == 'UAE Customs Clearance Expense (Excl. VAT Paid)').mapped('amount')
            )
            vat_paid_total = sum(
                charges.filtered(lambda c: c.product_id.name == 'VAT Paid at Customs Clearance (UAE)').mapped('amount')
            )
            bank_total = sum(
                charges.filtered(lambda c: c.product_id.name == 'Total UAE Bank Expenses').mapped('amount')
            )
            company_total = sum(
                charges.filtered(lambda c: c.product_id.name == 'Total UAE Company Expenses').mapped('amount')
            )
            courier_total = sum(
                charges.filtered(
                    lambda c: c.product_id.name == 'TDHL/TCS/Fedex etc. Docs Courier Charges to UAE Bank'
                ).mapped('amount')
            )
            line.uae_bank_expenses = bank_total * line.value_pct_share
            line.uae_company_expenses = company_total * line.value_pct_share
            line.uae_courier_charges = courier_total * line.value_pct_share
            line.freight_expense_origin_uae = freight_total * line.value_pct_share
            line.uae_customs_clearance_expense= customs_clearance_total * line.value_pct_share
            line.uae_vat_paid_customs_clearance = vat_paid_total * line.value_pct_share
    @api.depends(
        'freight_expense_origin_uae', 'uae_customs_clearance_expense',
        'uae_vat_paid_customs_clearance', 'uae_bank_expenses',
        'uae_company_expenses', 'uae_courier_charges', 'uae_any_other_expense',
    )
    def _compute_total_uae_expenses(self):
        for line in self:
            line.total_uae_expenses = _round_half_up(
                line.freight_expense_origin_uae
                + line.uae_customs_clearance_expense
                + line.uae_vat_paid_customs_clearance
                + line.uae_bank_expenses
                + line.uae_company_expenses
                + line.uae_courier_charges
                + line.uae_any_other_expense
            )
    
    # -- Pakistan Customs - Other Duty & Penalty Charges --
    pc_cess_sindh_excise_duty = fields.Float(
        string='CESS Sindh Excise Duty', compute='_compute_pc_other_duty_penalty', store=True,
        help="'CESS Sindh Excise Duty' entered under Local & Other Charges, apportioned by "
             "this line's Value % Share."
    )
    pc_sindh_stamp_duty = fields.Float(
        string='Sindh Stamp Duty', compute='_compute_pc_other_duty_penalty', store=True,
        help="'Sindh Stamp Duty' entered under Local & Other Charges, apportioned by this "
             "line's Value % Share."
    )
    pc_psw_gd_fee = fields.Float(
        string='PSW GD Fee', compute='_compute_pc_other_duty_penalty', store=True,
        help="'PSW GD Fee' entered under Local & Other Charges, apportioned by this line's "
             "Value % Share."
    )
    pc_invoice_not_found_penalty = fields.Float(
        string='Invoice Not Found Penalty', compute='_compute_pc_other_duty_penalty', store=True,
        help="'Invoice Not Found Penalty' entered under Local & Other Charges, apportioned "
             "by this line's Value % Share."
    )
    pc_any_other_charges = fields.Float(
        string='Any Other Charges', compute='_compute_pc_other_duty_penalty', store=True,
        help="'Any Other Charges' entered under Local & Other Charges, apportioned by this "
             "line's Value % Share."
    )

    @api.depends(
            'value_pct_share',
            'master_id.charge_line_ids.amount', 'master_id.charge_line_ids.product_id',
        )
    def _compute_pc_other_duty_penalty(self):
        for line in self:
            charges = line.master_id.charge_line_ids

            def _total_for(name):
                return sum(charges.filtered(lambda c: c.product_id.name == name).mapped('amount'))

            line.pc_cess_sindh_excise_duty = _round_half_up(_total_for('CESS Sindh Excise Duty') * line.value_pct_share)
            line.pc_sindh_stamp_duty = _round_half_up(_total_for('Sindh Stamp Duty') * line.value_pct_share)
            line.pc_psw_gd_fee = _round_half_up(_total_for('PSW GD Fee') * line.value_pct_share)
            line.pc_invoice_not_found_penalty = _round_half_up(_total_for('Invoice Not Found Penalty') * line.value_pct_share)
            line.pc_any_other_charges = _round_half_up(_total_for('Any Other Charges') * line.value_pct_share)


    tariff_line_id = fields.Many2one(
        'tdc.import.tariff.line', string='Source Tariff Line',
        help='The originating GD Tariff line this row was copied from — used to pull '
             'per-line duty/tax figures.'
    )
  

    customs_duty_line = fields.Float(
        string='Customs Duty (CD+RD+ACD)', compute='_compute_duty_tax_line', store=True
    )
    sales_tax_line = fields.Float(
        string='Sales Tax (ST+AST)', compute='_compute_duty_tax_line', store=True
    )
    income_tax_line = fields.Float(
        string='Income Tax (IT)', compute='_compute_duty_tax_line', store=True
    )
    total_duty_tax_line = fields.Float(
        string='TOTAL Duty Taxes', compute='_compute_duty_tax_line', store=True
    )

    @api.depends(
        'tariff_line_id.cd_pkr', 'tariff_line_id.rd_pkr', 'tariff_line_id.acd_pkr',
        'tariff_line_id.st_pkr', 'tariff_line_id.ast_pkr', 'tariff_line_id.it_pkr',
        'tariff_line_id.total_payable_pkr',
    )
    def _compute_duty_tax_line(self):
        for line in self:
            tl = line.tariff_line_id
            line.customs_duty_line = (tl.cd_pkr + tl.rd_pkr + tl.acd_pkr) if tl else 0.0
            line.sales_tax_line = (tl.st_pkr + tl.ast_pkr) if tl else 0.0
            line.income_tax_line = tl.it_pkr if tl else 0.0
            line.total_duty_tax_line = tl.total_payable_pkr if tl else 0.0

    # -- Expenses at Destination Port/Airport --
    dest_godown_shed_charges = fields.Float(
        string='Godown/Shed Charge', compute='_compute_dest_port_expenses', store=True
    )
    dest_delivery_order_charges = fields.Float(
        string='Delivery Order DO Charges', compute='_compute_dest_port_expenses', store=True
    )
    dest_psw_token_gd_submission = fields.Float(
        string='PSW Token for GD Submission', compute='_compute_dest_port_expenses', store=True
    )
    dest_caa_charges = fields.Float(
        string='Civil Aviation CAA Charges (if By Air)', compute='_compute_dest_port_expenses', store=True
    )
    dest_transport_port_warehouse = fields.Float(
        string='Transport Exp from Port/Airport to Welkin Warehouse',
        compute='_compute_dest_port_expenses', store=True
    )
    dest_clearing_agent_fees = fields.Float(
        string='Clearing Agent Fees', compute='_compute_dest_port_expenses', store=True
    )
    dest_misc_examination_expense = fields.Float(
        string='MISC. Examination Expense', compute='_compute_dest_port_expenses', store=True
    )
    dest_misc_assessment_expense = fields.Float(
        string='MISC. Assessment Expense', compute='_compute_dest_port_expenses', store=True
    )
    dest_misc_delivery_gateout_expense = fields.Float(
        string='MISC. Delivery/Gateout Expense', compute='_compute_dest_port_expenses', store=True
    )
    dest_any_other_expense_transport = fields.Float(
        string='Any Other Expense - Transportation/Bykea or Other',
        compute='_compute_dest_port_expenses', store=True
    )

    total_customs_clearance_cost_excl_st = fields.Float(
        string='TOTAL CUSTOMS CLEARANCE COST in PK (Excl. SALES TAX)',
        compute='_compute_total_customs_clearance_cost', store=True,
        help='Sum of Expenses at Destination Port/Airport + Pakistan Customs Other Duty & '
             'Penalty Charges + apportioned Customs Duty (CD+RD+ACD) + apportioned Income Tax (IT).'
    )
    total_customs_clearance_cost_incl_st = fields.Float(
        string='TOTAL CUSTOMS CLEARANCE COST in PK (Incl. SALES TAX)',
        compute='_compute_total_customs_clearance_cost', store=True,
        help='Sum of Expenses at Destination Port/Airport + Pakistan Customs Other Duty & '
             'Penalty Charges + apportioned TOTAL Duty & Taxes.'
    )

    @api.depends(
        'value_pct_share',
        'master_id.charge_line_ids.amount', 'master_id.charge_line_ids.product_id',
    )
    def _compute_dest_port_expenses(self):
        for line in self:
            charges = line.master_id.charge_line_ids

            def _total_for(name):
                return sum(charges.filtered(lambda c: c.product_id.name == name).mapped('amount'))

            line.dest_godown_shed_charges = _round_half_up(
                _total_for('Godown/Shed Charges') * line.value_pct_share)
            line.dest_delivery_order_charges = _round_half_up(
                _total_for('Delivery Order (DO) Charges') * line.value_pct_share)
            line.dest_psw_token_gd_submission = _round_half_up(
                _total_for('PSW Token for GD Submission') * line.value_pct_share)
            line.dest_caa_charges = _round_half_up(
                _total_for('Civil Aviation (CAA) Charges (if By Air)') * line.value_pct_share)
            line.dest_transport_port_warehouse = _round_half_up(
                _total_for('Transport Exp. from Port/Airport to Welkin Warehouse') * line.value_pct_share)
            line.dest_clearing_agent_fees = _round_half_up(
                _total_for('Clearing Agent Fees') * line.value_pct_share)
            line.dest_misc_examination_expense = _round_half_up(
                _total_for('MISC. Examination Expense') * line.value_pct_share)
            line.dest_misc_assessment_expense = _round_half_up(
                _total_for('MISC. Assessment Expense') * line.value_pct_share)
            line.dest_misc_delivery_gateout_expense = _round_half_up(
                _total_for('MISC. Delivery/Gate-out Expense') * line.value_pct_share)
            line.dest_any_other_expense_transport = _round_half_up(
                _total_for('Any Other Expense - Transportation/Bykea or Other') * line.value_pct_share)
    

    @api.depends(
        'dest_godown_shed_charges', 'dest_delivery_order_charges', 'dest_psw_token_gd_submission',
        'dest_caa_charges', 'dest_transport_port_warehouse', 'dest_clearing_agent_fees',
        'dest_misc_examination_expense', 'dest_misc_assessment_expense',
        'dest_misc_delivery_gateout_expense', 'dest_any_other_expense_transport',
        'pc_cess_sindh_excise_duty', 'pc_sindh_stamp_duty', 'pc_psw_gd_fee',
        'pc_invoice_not_found_penalty', 'pc_any_other_charges',
        'value_pct_share', 'customs_duty_line', 'income_tax_line',
        'total_duty_tax_line',
    )
    def _compute_total_customs_clearance_cost(self):
        for line in self:
            dest_expenses_total = (
                line.dest_godown_shed_charges + line.dest_delivery_order_charges
                + line.dest_psw_token_gd_submission + line.dest_caa_charges
                + line.dest_transport_port_warehouse + line.dest_clearing_agent_fees
                + line.dest_misc_examination_expense + line.dest_misc_assessment_expense
                + line.dest_misc_delivery_gateout_expense + line.dest_any_other_expense_transport
            )
            pc_total = (
                line.pc_cess_sindh_excise_duty + line.pc_sindh_stamp_duty + line.pc_psw_gd_fee
                + line.pc_invoice_not_found_penalty + line.pc_any_other_charges
            )
            customs_duty_apportioned = line.customs_duty_line
            income_tax_apportioned = line.income_tax_line 
            total_duty_tax_apportioned = line.total_duty_tax_line

            line.total_customs_clearance_cost_excl_st = _round_half_up(
                dest_expenses_total + pc_total + customs_duty_apportioned + income_tax_apportioned
            )
            line.total_customs_clearance_cost_incl_st = _round_half_up(
                dest_expenses_total + pc_total + total_duty_tax_apportioned
            ) 
    



    ##############################
    # -- Pakistan Customs - Duty & Taxes as per GD (per line, from the source tariff line) --
    # -- copied in automatically from the GD Tariff line on tariff_id change --
    
    # -- Grand Total Cost (Item Wise) --
    total_home_cost_excl_gst = fields.Float(
        string='UNIT HOME COST (Excl. GST)', compute='_compute_grand_total_cost', store=True,
        help='TOTAL CUSTOMS CLEARANCE COST in PK (Excl. SALES TAX) + TOTAL UAE EXPENSES '
             '+ TOTAL C&F KARACHI COST'
    )
    total_home_cost_incl_gst = fields.Float(
        string='TOTAL HOME COST (Incl. GST)', compute='_compute_grand_total_cost', store=True,
        help='TOTAL CUSTOMS CLEARANCE COST in PK (Incl. SALES TAX) + TOTAL UAE EXPENSES '
             '+ TOTAL C&F KARACHI COST'
    )
    unit_home_cost_incl_gst = fields.Float(
        string='UNIT HOME Cost (Incl. GST)', compute='_compute_grand_total_cost', store=True,
        help='TOTAL HOME COST (Incl. GST) / Qty'
    )

    @api.depends(
        'total_customs_clearance_cost_excl_st', 'total_customs_clearance_cost_incl_st',
        'total_uae_expenses', 'total_cf_karachi_cost', 'qty',
    )
    def _compute_grand_total_cost(self):
        for line in self:
            line.total_home_cost_excl_gst = _round_half_up(
                line.total_customs_clearance_cost_excl_st
                + line.total_uae_expenses
                + line.total_cf_karachi_cost
            )
            line.total_home_cost_incl_gst = _round_half_up(
                line.total_customs_clearance_cost_incl_st
                + line.total_uae_expenses
                + line.total_cf_karachi_cost
            )
            line.unit_home_cost_incl_gst = _round_half_up(
                line.total_home_cost_incl_gst / line.qty
            ) if line.qty else 0.0