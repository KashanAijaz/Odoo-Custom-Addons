# -*- coding: utf-8 -*-
from odoo import api, fields, models


class TdcTariffMenu(models.Model):
    _name = 'tdc.tariff.menu'
    _description = 'TDC Tariff Menu'
    _rec_name = 'gd_number'
    _order = 'gd_date desc, id desc'

    gd_number = fields.Char(string='GD Number', required=True)
    gd_date = fields.Date(string='GD Date')

    currency_id = fields.Many2one(
        'res.currency', string='Currency Import',
        help='Currency of import (USD, EUR, PKR, etc.).'
    )
    gd_exchange_rate = fields.Float(
        string='GD Payment Exchange Rate', digits=(16, 4),
        help='Exchange rate applicable at the time of GD payment. '
             'Entered manually since rates change frequently.'
    )

    insurance_percent = fields.Float(
        string='Insurance % (on CFR Value)', digits=(5, 2)
    )
    landing_charges_percent = fields.Float(
        string='Landing Charges % (on CFR Value)', digits=(5, 2)
    )

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )

    tariff_line_ids = fields.One2many(
        'tdc.tariff.line', 'tariff_menu_id', string='Tariff Lines'
    )

    # ------------------------------------------------------------------
    # Grand Total (mirrors the "GRAND TOTAL" row of the GD Tax Calc sheet)
    # ------------------------------------------------------------------
    total_assessed_value = fields.Float(
        string='Total Assessed Value (Foreign)',
        compute='_compute_totals', store=True, digits=(16, 2)
    )
    total_assessed_value_pkr = fields.Float(
        string='Total Assessed Value (PKR)',
        compute='_compute_totals', store=True, digits=(16, 2)
    )
    total_cd = fields.Float(
        string='Total CD (PKR)', compute='_compute_totals', store=True,
        digits=(16, 2)
    )
    total_rd = fields.Float(
        string='Total RD (PKR)', compute='_compute_totals', store=True,
        digits=(16, 2)
    )
    total_acd = fields.Float(
        string='Total ACD (PKR)', compute='_compute_totals', store=True,
        digits=(16, 2)
    )
    total_st = fields.Float(
        string='Total ST (PKR)', compute='_compute_totals', store=True,
        digits=(16, 2)
    )
    total_ast = fields.Float(
        string='Total AST (PKR)', compute='_compute_totals', store=True,
        digits=(16, 2)
    )
    total_it = fields.Float(
        string='Total IT (PKR)', compute='_compute_totals', store=True,
        digits=(16, 2)
    )
    total_payable = fields.Float(
        string='Grand Total Payable (PKR)', compute='_compute_totals',
        store=True, digits=(16, 2)
    )

    @api.depends(
        'tariff_line_ids.assessed_total_value',
        'tariff_line_ids.assessed_total_value_pkr',
        'tariff_line_ids.cd_amount',
        'tariff_line_ids.rd_amount',
        'tariff_line_ids.acd_amount',
        'tariff_line_ids.st_amount',
        'tariff_line_ids.ast_amount',
        'tariff_line_ids.it_amount',
        'tariff_line_ids.total_payable',
    )
    def _compute_totals(self):
        for menu in self:
            lines = menu.tariff_line_ids
            menu.total_assessed_value = sum(lines.mapped('assessed_total_value'))
            menu.total_assessed_value_pkr = sum(lines.mapped('assessed_total_value_pkr'))
            menu.total_cd = sum(lines.mapped('cd_amount'))
            menu.total_rd = sum(lines.mapped('rd_amount'))
            menu.total_acd = sum(lines.mapped('acd_amount'))
            menu.total_st = sum(lines.mapped('st_amount'))
            menu.total_ast = sum(lines.mapped('ast_amount'))
            menu.total_it = sum(lines.mapped('it_amount'))
            menu.total_payable = sum(lines.mapped('total_payable'))
