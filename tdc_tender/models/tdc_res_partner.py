from odoo import api, fields, models


class EndUser(models.Model):
    _name = 'end.user'
    _description = 'End User'
    _rec_name = 'name'

    name = fields.Char(string='End User', required=True)


class ResPartner(models.Model):
    _inherit = "res.partner"

    end_user_id = fields.Many2one(
        "res.users",
        string="Created By User",
        default=lambda self: self.env.user,
    )

    end_user = fields.Many2one(
        'end.user',
        string='End User',
    )

    type = fields.Selection(
        selection=[('contact', 'Contact')],
        string='Address Type',
        default='contact',
        ondelete={
            'invoice': 'set default',
            'delivery': 'set default',
            'other': 'set default',
        },
    )