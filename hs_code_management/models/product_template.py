# -*- coding: utf-8 -*-
from odoo import fields, models, api
from datetime import date 


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hs_code_id = fields.Many2one(
        'hs.code',
        string='HS Code',
        
    )

    sku = fields.Char(
        string="SKU"
    )

    # brand_id = fields.Char(
    #     string="Brand ID"
    # )

    expiry = fields.Boolean(
        string="Expiry"
    )

    expiry_date = fields.Date(
    string="Expiry Date"
    )

    type = fields.Selection(
        selection=[
            ('consu', 'Goods'),
            ('service', 'Service'),
        ],
        string='Type',
        default='consu',
    )

    model_no_id = fields.Many2one(
        'product.model',
        string='Model No',
    )
    
    serial_no_id = fields.Many2one(
        'product.serial',
        string='Serial No',
    )
    is_perishable = fields.Boolean(string="Perishable")

    days_to_expire = fields.Integer(
        string="Days to Expire",
        compute='_compute_days_to_expire',
        store=False,
    )

    @api.depends('expiry_date')
    def _compute_days_to_expire(self):
        today = date.today()
        for product in self:
            if product.expiry_date:
                delta = (product.expiry_date - today).days
                product.days_to_expire = delta
            else:
                product.days_to_expire = 0

