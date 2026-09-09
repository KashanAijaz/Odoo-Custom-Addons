# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    hs_code_id = fields.Many2one(
        "hs.code",
        related="product_tmpl_id.hs_code_id",
        string="HS Code",
        store=True,
        readonly=True,
    )

    model_no_id = fields.Many2one(
        'product.model',
        related="product_tmpl_id.model_no_id",
        string='Model No',
    )
    
    serial_no_id = fields.Many2one(
        'product.serial',
        related="product_tmpl_id.serial_no_id",
        string='Serial No',
    )


