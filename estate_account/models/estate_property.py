from odoo import fields, models


class EstateProperty(models.Model):
    _inherit = "estate.property"

    invoice_id = fields.Many2one(
        "account.move",
        string="Invoice",
        copy=False,
    )

    def action_sold(self):
        for record in self:
            invoice = self.env["account.move"].create({
                "partner_id": record.buyer_id.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (0, 0, {
                        "name": record.name,
                        "quantity": 1,
                        "price_unit": record.selling_price * 0.06,
                    }),
                    (0, 0, {
                        "name": "Administrative Fees",
                        "quantity": 1,
                        "price_unit": 100.00,
                    }),
                ],
            })
            record.invoice_id = invoice
        return super().action_sold()

    def action_view_invoice(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Invoice",
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": self.invoice_id.id,
        }