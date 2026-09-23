from odoo import fields, models


class AzezemThanPrint(models.Model):
    _name = 'azezem.than.print'
    _description = 'Azezem Than Print'
    _rec_name = 'than_number'

    than_number = fields.Char(string='Than Number')
    product_id = fields.Many2one('product.product', string='Product')
    categ_id = fields.Many2one(
        'product.category',
        string='Category',
        related='product_id.categ_id',
        store=True,
        readonly=True,
    )

    def action_print_than(self):
        self.ensure_one()
        return self.env.ref('azezem_than_print.action_report_than_print').report_action(self)