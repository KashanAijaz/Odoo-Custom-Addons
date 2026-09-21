# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    weight_kg_ft = fields.Float(string='Weight Kg./Ft.', digits=(16, 4))