from odoo import fields, models
from odoo.exceptions import UserError


class TDCCreateLoaWizard(models.TransientModel):
    _name = "tdc.create.loa.wizard"
    _description = "Create More Letter of Acceptance Wizard"

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        required=True,
    )

    loa_count = fields.Integer(
        string="Number of Letter of Acceptance",
        default=1,
        required=True,
    )

    def action_create_loa(self):
        self.ensure_one()

        if self.loa_count <= 0:
            raise UserError("Please enter a number greater than 0.")

        sale_order = self.sale_order_id
        new_orders = self.env["sale.order"]

        for i in range(self.loa_count):
            new_order = sale_order.copy({
                "tender_workflow_state": "letter_of_acceptance",
                "technical_evaluation_line_ids": [],
                "financial_evaluation_line_ids": [],
                "loa_line_ids": [],
            })
            new_orders |= new_order

        action = {
            "type": "ir.actions.act_window",
            "name": "Letter of Acceptance Orders",
            "res_model": "sale.order",
            "view_mode": "list,form",
            "views": [
                (self.env.ref("sale.view_quotation_tree_with_onboarding").id, "list"),
                (False, "form"),
            ],
            "domain": [("id", "in", new_orders.ids)],
            "target": "current",
        }
        return action