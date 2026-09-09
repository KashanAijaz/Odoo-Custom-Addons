from odoo import api, fields, models


class EndUser(models.Model):
    _name = 'end.user'
    _description = 'Department'
    _rec_name = 'name'

    name = fields.Char(string='Department', required=True)


class ResPartner(models.Model):
    _inherit = "res.partner"

    end_user_id = fields.Many2one(
        "res.users",
        string="Created By User",
        default=lambda self: self.env.user,
    )

    end_user = fields.Many2one(
        'end.user',
        string='Department',
    )

    # is_it_end_user = fields.Boolean(
    #     string='Is It End User',
    #     default=False,
    # )

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