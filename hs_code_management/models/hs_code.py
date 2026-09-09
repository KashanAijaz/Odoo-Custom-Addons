# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class HsCode(models.Model):
    _name = 'hs.code'
    _description = 'HS Code'
    _rec_name = 'code'
    _order = 'code'

    code = fields.Char(
        string='HS Code',
        required=True,
        index=True,
        help="Format: 1000.2000"
    )

    description = fields.Char(
        string='Description',
        required=True
    )
    st_id = fields.Many2one(
        'account.tax',
        string='Sales Tax',
 
    )

    ast_id = fields.Many2one(
        'account.tax',
        string='Additional Sales Tax',
        
    )

    it_id = fields.Many2one(
        'account.tax',
        string='Income Tax',
       
    )

    # Duty Percentages
    cd_percentage = fields.Float(
        string='CD %',
        digits=(16, 2)
    )

    rd_percentage = fields.Float(
        string='RD %',
        digits=(16, 2)
    )

    acd_percentage = fields.Float(
        string='ACD %',
        digits=(16, 2)
    )

    # Chart of Accounts
    cd_account_id = fields.Many2one(
        'account.account',
        string='CD COA',
  
    )

    rd_account_id = fields.Many2one(
        'account.account',
        string='RD COA',
        
    )

    acd_account_id = fields.Many2one(
        'account.account',
        string='ACD COA',
      
    )

    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'This HS Code already exists!'),
    ]

    @api.constrains('code')
    def _check_hs_code_format(self):
        """
        Valid format:
            1000.2000
            3920.1000
            8504.4010
        """
        pattern = r'^\d{4}\.\d{4}$'
        for rec in self:
            if rec.code and not re.match(pattern, rec.code):
                raise ValidationError(
                    "HS Code must be in the format ####.#### (e.g. 1000.2000)."
                )

class ProductModel(models.Model):
    _name = 'product.model'
    _description = 'Product Model'
    
    name = fields.Char(string='Model Name', required=True)
    code = fields.Char(string='Model Code')
    
class ProductSerial(models.Model):
    _name = 'product.serial'
    _description = 'Product Serial'
    
    name = fields.Char(string='Serial Number', required=True)
    model_id = fields.Many2one('product.model', string='Model')
