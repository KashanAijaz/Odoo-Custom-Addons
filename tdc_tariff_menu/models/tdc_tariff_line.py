# -*- coding: utf-8 -*-
from odoo import api, fields, models


class TdcTariffLine(models.Model):
    _name = 'tdc.tariff.line'
    _description = 'TDC Tariff Line'
    _order = 'id'

    tariff_menu_id = fields.Many2one(
        'tdc.tariff.menu', string='Tariff Menu',
        required=True, ondelete='cascade', index=True
    )

    product_id = fields.Many2one(
        'product.template', 
        string='Item Description', required=True
    )

    hs_code_id = fields.Many2one(
        'hs.code',
        string="HS Code"
    )

    # ------------------------------------------------------------------
    # Auto-populated from the product (related fields refresh automatically
    # whenever product_id changes, including inline in the editable list).
    # ------------------------------------------------------------------
    hs_code = fields.Char(
        related='product_id.hs_code_id.code',
        string='HS Code', store=True, readonly=True
    )
    uom_id = fields.Many2one(
        related='product_id.uom_id',
        string='UOM', store=True, readonly=True
    )
    cd = fields.Float(
        related='product_id.hs_code_id.cd',
        string='CD %',
        store=True,
        readonly=True,
    )

    acd = fields.Float(
        related='product_id.hs_code_id.acd',
        string='ACD %',
        store=True,
        readonly=True,
    )

    rd = fields.Float(
        related='product_id.hs_code_id.rd',
        string='RD %',
        store=True,
        readonly=True,
    )

    # Taxes from the product, split by TDC Tax Category.
    # Each stored Many2many needs its OWN relation table — otherwise Odoo
    # tries to reuse the same auto-generated table for more than one of
    # these fields (since they all point at the same comodel) and fails
    # to load with "use the same table and columns".
    sales_tax_ids = fields.Many2many(
        'account.tax',
        relation='tdc_tariff_line_sales_tax_rel',
        column1='tariff_line_id', column2='tax_id',
        compute='_compute_categorized_taxes', store=True,
        string='Sales Tax' ,
        readonly = False
    )
    advance_sales_tax_ids = fields.Many2many(
        'account.tax',
        relation='tdc_tariff_line_advance_sales_tax_rel',
        column1='tariff_line_id', column2='tax_id',
        compute='_compute_categorized_taxes', store=True,
        string='Advance Sales Tax',
        readonly = False
    )
    income_tax_ids = fields.Many2many(
        'account.tax',
        relation='tdc_tariff_line_income_tax_rel',
        column1='tariff_line_id', column2='tax_id',
        compute='_compute_categorized_taxes', store=True,
        string='Income Tax',
        readonly = False
    )

    st_percent = fields.Float(
        string='ST %', compute='_compute_tax_percentages', store=True,
        digits=(16, 2)
    )
    ast_percent = fields.Float(
        string='AST %', compute='_compute_tax_percentages', store=True,
        digits=(16, 2)
    )
    it_percent = fields.Float(
        string='IT %', compute='_compute_tax_percentages', store=True,
        digits=(16, 2)
    )

    # ------------------------------------------------------------------
    # User input
    # ------------------------------------------------------------------
    qty = fields.Float(
        string='Qty', default=1.0, digits=(16, 3),
        help='Quantity of this item on the GD.'
    )
    assessed_unit_value = fields.Float(
        string='Assessed Unit Value (Foreign)', digits=(16, 4),
        help='Unit value in the foreign import currency (e.g. EUR/USD), '
             'as entered by the user.'
    )

    # ------------------------------------------------------------------
    # Computed values (mirrors the GD Tax Calculation sheet)
    # ------------------------------------------------------------------
    assessed_total_value = fields.Float(
        string='Assessed Total Value (Foreign)',
        compute='_compute_amounts', store=True, digits=(16, 2),
        help='Qty x Assessed Unit Value, in the foreign currency.'
    )
    assessed_unit_value_pkr = fields.Float(
        string='Assessed Unit Value (PKR)',
        compute='_compute_amounts', store=True, digits=(16, 2),
        help='Assessed Unit Value x GD Exchange Rate x (1 + Insurance %) '
             'x (1 + Landing Charges %), rounded.'
    )
    assessed_total_value_pkr = fields.Float(
        string='Assessed Total Value (PKR)',
        compute='_compute_amounts', store=True, digits=(16, 2),
        help='Assessed Unit Value (PKR) x Qty.'
    )

    cd_amount = fields.Float(
        string='CD (PKR)', compute='_compute_amounts', store=True,
        digits=(16, 2)
    )
    rd_amount = fields.Float(
        string='RD (PKR)', compute='_compute_amounts', store=True,
        digits=(16, 2)
    )
    acd_amount = fields.Float(
        string='ACD (PKR)', compute='_compute_amounts', store=True,
        digits=(16, 2)
    )
    st_amount = fields.Float(
        string='ST (PKR)', compute='_compute_amounts', store=True,
        digits=(16, 2)
    )
    ast_amount = fields.Float(
        string='AST (PKR)', compute='_compute_amounts', store=True,
        digits=(16, 2)
    )
    it_amount = fields.Float(
        string='IT (PKR)', compute='_compute_amounts', store=True,
        digits=(16, 2)
    )
    total_payable = fields.Float(
        string='Total Sum Payable (PKR)', compute='_compute_amounts',
        store=True, digits=(16, 2),
        help='CD + RD + ACD + ST + AST + IT, in PKR.'
    )

    @api.depends('product_id', 'product_id.taxes_id',
                 'product_id.taxes_id.tdc_tax_category')
    def _compute_categorized_taxes(self):
        for line in self:
            taxes = line.product_id.taxes_id
            line.sales_tax_ids = taxes.filtered(
                lambda t: t.tdc_tax_category == 'sales')
            line.advance_sales_tax_ids = taxes.filtered(
                lambda t: t.tdc_tax_category == 'advance_sales')
            line.income_tax_ids = taxes.filtered(
                lambda t: t.tdc_tax_category == 'income')

    @api.depends('sales_tax_ids', 'advance_sales_tax_ids', 'income_tax_ids',
                 'sales_tax_ids.amount', 'advance_sales_tax_ids.amount',
                 'income_tax_ids.amount')
    def _compute_tax_percentages(self):
        for line in self:
            line.st_percent = sum(line.sales_tax_ids.mapped('amount'))
            line.ast_percent = sum(line.advance_sales_tax_ids.mapped('amount'))
            line.it_percent = sum(line.income_tax_ids.mapped('amount'))

    @api.depends(
        'qty', 'assessed_unit_value', 'cd', 'rd', 'acd',
        'st_percent', 'ast_percent', 'it_percent',
        'tariff_menu_id.gd_exchange_rate',
        'tariff_menu_id.insurance_percent',
        'tariff_menu_id.landing_charges_percent',
    )
    def _compute_amounts(self):
        for line in self:
            menu = line.tariff_menu_id
            rate = menu.gd_exchange_rate or 0.0
            insurance = (menu.insurance_percent or 0.0) / 100.0
            landing = (menu.landing_charges_percent or 0.0) / 100.0

            # Foreign currency values
            assessed_total_value = line.qty * line.assessed_unit_value
            line.assessed_total_value = assessed_total_value

            # PKR conversion: Unit Value x Rate x (1+Insurance%) x (1+Landing%)
            assessed_unit_value_pkr = round(
                line.assessed_unit_value * rate * (1 + insurance) * (1 + landing), 0
            )
            line.assessed_unit_value_pkr = assessed_unit_value_pkr

            assessed_total_value_pkr = assessed_unit_value_pkr * line.qty
            line.assessed_total_value_pkr = assessed_total_value_pkr

            # Duties (on Assessed Total Value in PKR)
            cd_amount = round(assessed_total_value_pkr * (line.cd or 0.0) / 100.0, 0)
            rd_amount = round(assessed_total_value_pkr * (line.rd or 0.0) / 100.0, 0)
            acd_amount = round(assessed_total_value_pkr * (line.acd or 0.0) / 100.0, 0)
            line.cd_amount = cd_amount
            line.rd_amount = rd_amount
            line.acd_amount = acd_amount

            duty_base = assessed_total_value_pkr + cd_amount + rd_amount + acd_amount

            # Taxes (ST and AST on duty-inclusive value; IT on top of that)
            st_amount = round(duty_base * (line.st_percent or 0.0) / 100.0, 0)
            ast_amount = round(duty_base * (line.ast_percent or 0.0) / 100.0, 0)
            line.st_amount = st_amount
            line.ast_amount = ast_amount

            it_amount = round(
                (duty_base + st_amount + ast_amount) * (line.it_percent or 0.0) / 100.0, 0
            )
            line.it_amount = it_amount

            line.total_payable = (
                cd_amount + rd_amount + acd_amount + st_amount + ast_amount + it_amount
            )
