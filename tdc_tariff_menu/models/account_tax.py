# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    tdc_tax_category = fields.Selection(
        [
            ('sales', 'Sales Tax'),
            ('advance_sales', 'Advance Sales Tax'),
            ('income', 'Income Tax'),
            ('other', 'Other'),
        ],
        string='TDC Tax Category',
        default='other',
        help='Used by the Tariff Menu module to automatically group this '
             'tax under Sales Tax / Advance Sales Tax / Income Tax on '
             'tariff lines. Set this once per tax and it will be picked '
             'up automatically wherever this tax is applied to a product.'
    )
