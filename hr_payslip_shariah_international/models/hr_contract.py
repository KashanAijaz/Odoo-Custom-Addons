# -*- coding: utf-8 -*-
from odoo import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    payroll_type = fields.Selection(
        selection=[
            ('shariah', 'Shariah Payroll System'),
            ('international', 'International Payroll System'),
        ],
        string="Payroll System",
        default='international',
        help="Determines how late minutes, day-off and sandwich leave "
             "deductions are calculated for payslips generated from this "
             "contract.",
    )
