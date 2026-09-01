# -*- coding: utf-8 -*-
from odoo import models, fields, api
from math import floor


def _round_half_up(value):
    """Round to the nearest whole number: .00-.49 rounds down,
    .50-.99 rounds up (unlike Python's banker's rounding)."""
    if not value:
        return 0.0
    integer = floor(value)
    decimal = round((value - integer) * 100)
    if decimal >= 50:
        return float(integer + 1)
    return float(integer)


class TdcImportTariff(models.Model):
    _name = 'tdc.import.tariff'
    _description = 'Import GD Tariff'
    _order = 'gd_date desc, id desc'
    _rec_name = 'dg_no'

    dg_no = fields.Char(string='GD No.', required=True, copy=False)
    gd_date = fields.Date(string='GD Date', required=True, default=fields.Date.context_today)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Number',
        domain="[('partner_id', '=', partner_id)]",
        help='Select a Purchase Order to pull its products, HS Codes and unit prices '
             'into the tariff lines below.'
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency of Import', required=True,
        help='Currency in which the assessed values are declared (EUR, USD, etc.).'
    )
    pkr_currency_id = fields.Many2one(
        'res.currency', string='PKR Currency', compute='_compute_pkr_currency_id', store=True
    )
    exchange_rate = fields.Float(
        string='GD Payment Exchange Rate', digits=(16, 4), required=True,
        help='Exchange rate used to convert the assessed value into PKR.'
    )
    insurance_percentage = fields.Float(
        string='Insurance % (on CFR value)', default=1.0
    )
    landing_charges_percentage = fields.Float(
        string='Landing Charges % (on CFR value)', default=1.0
    )
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company
    )
    notes = fields.Text(string='Notes')

    line_ids = fields.One2many(
        'tdc.import.tariff.line', 'tariff_id', string='Tariff Lines', copy=True
    )

    line_count = fields.Integer(string='Lines', compute='_compute_line_count')

    amount_assessed_total = fields.Float(string='Total Assessed Value', compute='_compute_totals', store=True)
    amount_assessed_total_pkr = fields.Float(string='Total Assessed Value (PKR)', compute='_compute_totals', store=True)
    amount_cd_total = fields.Float(string='Total CD (PKR)', compute='_compute_totals', store=True)
    amount_rd_total = fields.Float(string='Total RD (PKR)', compute='_compute_totals', store=True)
    amount_acd_total = fields.Float(string='Total ACD (PKR)', compute='_compute_totals', store=True)
    amount_st_total = fields.Float(string='Total ST (PKR)', compute='_compute_totals', store=True)
    amount_ast_total = fields.Float(string='Total AST (PKR)', compute='_compute_totals', store=True)
    amount_it_total = fields.Float(string='Total IT (PKR)', compute='_compute_totals', store=True)
    amount_total_payable = fields.Float(string='Total Sum Payable (PKR)', compute='_compute_totals', store=True)

    #######################
    ### Kashan ############

    @api.onchange('purchase_order_id')
    def _onchange_purchase_order_id(self):
        if not self.purchase_order_id:
            return

        lines_data = [(5, 0, 0)]  # clear existing lines first
        for po_line in self.purchase_order_id.order_line:
            if po_line.display_type:
                continue

            product = po_line.product_id
            hes = False
            if product:
                hes = product.hs_code_id or product.product_tmpl_id.hs_code_id

            lines_data.append((0, 0, {
                'product_id': product.id,
                'description': po_line.name,
                'hs_code_id': hes.id if hes else 0.0,
                'model_no_id': po_line.model_no_id.id if po_line.model_no_id else False,   # <-- YE LINE ADD KI
                'qty': po_line.product_qty,
                'uom_id': po_line.product_uom_id.id,
                'price_unit': po_line.price_unit,
                'cd_percentage': hes.cd_percentage if hes else 0.0,
                'rd_percentage': hes.rd_percentage if hes else 0.0,
                'acd_percentage': hes.acd_percentage if hes else 0.0,
                'st_tax_id': hes.st_id.id if hes and hes.st_id else False,
                'ast_tax_id': hes.ast_id.id if hes and hes.ast_id else False,
                'it_tax_id': hes.it_id.id if hes and hes.it_id else False,
            }))

        self.line_ids = lines_data

    #####################################
    @api.depends('company_id')
    def _compute_pkr_currency_id(self):
        pkr = self.env['res.currency'].search([('name', '=', 'PKR')], limit=1)
        for rec in self:
            rec.pkr_currency_id = pkr.id if pkr else False

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.depends(
        'line_ids.assessed_total_value',
        'line_ids.assessed_total_value_pkr',
        'line_ids.cd_pkr',
        'line_ids.rd_pkr',
        'line_ids.acd_pkr',
        'line_ids.st_pkr',
        'line_ids.ast_pkr',
        'line_ids.it_pkr',
        'line_ids.total_payable_pkr',
    )
    def _compute_totals(self):
        for rec in self:
            lines = rec.line_ids
            rec.amount_assessed_total = sum(lines.mapped('assessed_total_value'))
            rec.amount_assessed_total_pkr = sum(lines.mapped('assessed_total_value_pkr'))
            rec.amount_cd_total = sum(lines.mapped('cd_pkr'))
            rec.amount_rd_total = sum(lines.mapped('rd_pkr'))
            rec.amount_acd_total = sum(lines.mapped('acd_pkr'))
            rec.amount_st_total = sum(lines.mapped('st_pkr'))
            rec.amount_ast_total = sum(lines.mapped('ast_pkr'))
            rec.amount_it_total = sum(lines.mapped('it_pkr'))
            rec.amount_total_payable = sum(lines.mapped('total_payable_pkr'))


class TdcImportTariffLine(models.Model):
    _name = 'tdc.import.tariff.line'
    _description = 'Import GD Tariff Line'
    _order = 'sequence, id'

    tariff_id = fields.Many2one(
        'tdc.import.tariff', string='Tariff', required=True, ondelete='cascade'
    )
    sequence = fields.Integer(default=10)

    product_id = fields.Many2one('product.product', string='Item', required=True)
    # brand_id = fields.Many2one(
    #     related='product_id.product_tmpl_id.brand_id',
    #     string='Brand',
    #     store=True,
    #     readonly=False,
    # )
    description = fields.Char(string='Item Description')
    hs_code_id = fields.Many2one('hs.code', string='HS Code')
    model_no_id = fields.Many2one('product.model', string='Model No')   # <-- NAYA FIELD
    qty = fields.Float(string='Qty', default=1.0, required=True)
    uom_id = fields.Many2one('uom.uom', string='UOM')
    #kashan#
    price_unit = fields.Float(
        string='Unit Price',
        digits='Product Price',
        help='Unit price of the item (similar to Unit Price on Purchase Order lines).'
    )

    tariff_currency_id = fields.Many2one(
        related='tariff_id.currency_id', string='Currency', store=True, readonly=True
    )
    pkr_currency_id = fields.Many2one(
        related='tariff_id.pkr_currency_id', string='PKR', store=True, readonly=True
    )
    exchange_rate = fields.Float(related='tariff_id.exchange_rate', string='Exchange Rate', readonly=True)
    insurance_percentage = fields.Float(
        related='tariff_id.insurance_percentage', string='Insurance %', readonly=True
    )
    landing_charges_percentage = fields.Float(
        related='tariff_id.landing_charges_percentage', string='Landing %', readonly=True
    )

    # Assessed values
    assessed_unit_value = fields.Float(
        string='Assessed Unit Value', digits=(16, 2 ),
        help='Assessed unit value in the Currency of Import (e.g. EUR/USD), entered manually.'
    )
    assessed_total_value = fields.Float(
        string='Assessed Total Value', compute='_compute_assessed_values', store=True,
        help='Assessed Unit Value * Qty (in Currency of Import).'
    )
    assessed_unit_value_pkr = fields.Float(
        string='Assessed Unit Value (PKR)', compute='_compute_assessed_values', store=True,
        help='Assessed Unit Value * Exchange Rate * (1 + Insurance %) * (1 + Landing Charges %), '
             'rounded to the nearest whole rupee (half-up).'
    )
    assessed_total_value_pkr = fields.Float(
        string='Assessed Total Value (PKR)', compute='_compute_assessed_values', store=True,
        help='Assessed Unit Value (PKR) * Qty, rounded to the nearest whole rupee (half-up). '
             'This is the customs value used as the base for all duties/taxes below.'
    )

    # Duties, from HS Code
    cd_percentage = fields.Float(string='CD %', digits=(16, 2))
    cd_pkr = fields.Float(string='CD (PKR)', compute='_compute_duties', store=True)

    rd_percentage = fields.Float(string='RD %', digits=(16, 2))
    rd_pkr = fields.Float(string='RD (PKR)', compute='_compute_duties', store=True)

    acd_percentage = fields.Float(string='ACD %', digits=(16, 2))
    acd_pkr = fields.Float(string='ACD (PKR)', compute='_compute_duties', store=True)

    # Taxes, from account.tax
    st_tax_id = fields.Many2one(
        'account.tax', string='ST', domain=[('type_tax_use', '=', 'purchase')]
    )
    st_percentage = fields.Float(
        string='ST %', digits=(16, 2),
        compute='_compute_tax_percentages', store=True, readonly=False,
    )
    st_pkr = fields.Float(string='ST (PKR)', compute='_compute_duties', store=True)

    ast_tax_id = fields.Many2one(
        'account.tax', string='AST', domain=[('type_tax_use', '=', 'purchase')]
    )
    ast_percentage = fields.Float(
        string='AST %', digits=(16, 2),
        compute='_compute_tax_percentages', store=True, readonly=False,
    )
    ast_pkr = fields.Float(string='AST (PKR)', compute='_compute_duties', store=True)

    it_tax_id = fields.Many2one(
        'account.tax', string='IT', domain=[('type_tax_use', '=', 'purchase')]
    )
    it_percentage = fields.Float(
        string='IT %', digits=(16, 2),
        compute='_compute_tax_percentages', store=True, readonly=False,
    )
    it_pkr = fields.Float(string='IT (PKR)', compute='_compute_duties', store=True)

    total_payable_pkr = fields.Float(
        string='Total Sum Payable (PKR)', compute='_compute_duties', store=True
    )

    # ---------------------------------------------------------
    # Onchange helpers
    # ---------------------------------------------------------
   
    @api.onchange('hs_code_id')
    def _onchange_hs_code_id(self):
        for line in self:
            line._apply_hs_code_percentages()

    def _apply_hs_code_percentages(self):
        for line in self:
            hs = line.hs_code_id
            line.cd_percentage = hs.cd_percentage if hs else 0.0
            line.rd_percentage = hs.rd_percentage if hs else 0.0
            line.acd_percentage = hs.acd_percentage if hs else 0.0
            line.st_tax_id = hs.st_id if hs else False
            line.ast_tax_id = hs.ast_id if hs else False
            line.it_tax_id = hs.it_id if hs else False
    @api.depends('st_tax_id', 'ast_tax_id', 'it_tax_id')
    def _compute_tax_percentages(self):
        for line in self:
            line.st_percentage = line.st_tax_id.amount if line.st_tax_id else 0.0
            line.ast_percentage = line.ast_tax_id.amount if line.ast_tax_id else 0.0
            line.it_percentage = line.it_tax_id.amount if line.it_tax_id else 0.0
            
    # ---------------------------------------------------------
    # Computes
    # ---------------------------------------------------------
    @api.depends(
        'qty', 'assessed_unit_value', 'exchange_rate',
        'insurance_percentage', 'landing_charges_percentage',
    )
    def _compute_assessed_values(self):
        for line in self:
            line.assessed_total_value = line.qty * line.assessed_unit_value

            factor = (1 + (line.insurance_percentage or 0.0) / 100.0) * \
                     (1 + (line.landing_charges_percentage or 0.0) / 100.0)
            raw_unit_value_pkr = line.assessed_unit_value * line.exchange_rate * factor

            # Custom rounding: .00-.49 rounds down, .50-.99 rounds up
            line.assessed_unit_value_pkr = _round_half_up(raw_unit_value_pkr)
            line.assessed_total_value_pkr = _round_half_up(line.assessed_unit_value_pkr * line.qty)

    @api.depends(
        'assessed_total_value_pkr', 'cd_percentage', 'rd_percentage', 'acd_percentage',
        'st_percentage', 'ast_percentage', 'it_percentage',
    )
    def _compute_duties(self):
        for line in self:
            base = line.assessed_total_value_pkr

            # Calculate CD, RD, ACD based on base value
            line.cd_pkr = _round_half_up(base * (line.cd_percentage or 0.0) / 100.0)
            line.rd_pkr = _round_half_up(base * (line.rd_percentage or 0.0) / 100.0)
            line.acd_pkr = _round_half_up(base * (line.acd_percentage or 0.0) / 100.0)

            # Calculate value for ST and AST (base + CD + RD + ACD)
            value_for_st_ast = base + line.cd_pkr + line.rd_pkr + line.acd_pkr

            # Calculate ST and AST
            line.st_pkr = _round_half_up(value_for_st_ast * (line.st_percentage or 0.0) / 100.0)
            line.ast_pkr = _round_half_up(value_for_st_ast * (line.ast_percentage or 0.0) / 100.0)

            # Calculate value for IT (base + CD + RD + ACD + ST + AST)
            value_for_it = base + line.cd_pkr + line.rd_pkr + line.acd_pkr + line.st_pkr + line.ast_pkr

            # Calculate IT on the cumulative value
            line.it_pkr = _round_half_up(value_for_it * (line.it_percentage or 0.0) / 100.0)

            # Calculate total payable (base + all duties)
            line.total_payable_pkr = (
                line.cd_pkr + line.rd_pkr + line.acd_pkr +
                line.st_pkr + line.ast_pkr + line.it_pkr
            )
    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.description = line.product_id.name
                line.uom_id = line.product_id.uom_id
                line.hs_code_id = line.product_id.hs_code_id
                line.price_unit = line.product_id.standard_price  # <-- ye add karein
                line._apply_hs_code_percentages()