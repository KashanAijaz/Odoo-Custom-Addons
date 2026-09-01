from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError

class TDCTenderAttachmentLine(models.Model):
    _name = 'tdc.tender.attachment.line'
    _description = 'Tender Attachment Line'

    tender_id = fields.Many2one(
        'tdc.tender',
        string='Tender',
        required=True,
        # ondelete='cascade'
    )
    
    tender_ids = fields.Many2many(
        "tdc.tender",
        string="Tenders",
    )
    # YOUR EXACT SAME FIELDS + payment_note
    payment_attachment = fields.Binary(
        string="Payment Proof",
        attachment=True,
    )
    payment_attachment_filename = fields.Char(
        string="Attachment Name"
    )
    payment_note = fields.Text(
        string="Note"
    )
    
    # Instrument fields for each attachment
    instrument_type = fields.Selection(
        [
            ('online', 'Online'),
            ('pay_order', 'Pay Order'),
            ('cdr', 'CDR'),
            ('sdr', 'SDR'),
            ('bank_guarantee', 'Bank Guarantee'),
            ('cash', 'Cash'),
        ],
        string="Instrument Type",
        default="cash"
    )
    payment_ref = fields.Char(
        string="Payment Ref"
    )
    instrument_number = fields.Char(
        string="Instrument Number",
    )

    instrument_date = fields.Date(
        string="Instrument Date",
    )

    bank_name = fields.Char(
        string="Bank Name",
    )

    branch_name = fields.Char(
        string="Branch Name",
    )
    @api.onchange('instrument_type')
    def _onchange_instrument_type(self):
        """Clear fields when instrument type is online or cash"""
        if self.instrument_type in ['online', 'cash']:
            self.instrument_number = False
            self.instrument_date = False
            self.bank_name = False
            self.branch_name = False
        else:
            # Fields remain visible
            pass



class TDCTender(models.Model):
    _name = "tdc.tender"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Tender"

    name = fields.Char(
        string="Tender No.",
        required=True,
        copy=False,
        readonly=True,
        default="New",
    )

    upcoming_tender_id = fields.Many2one(
        "tdc.upcoming.tender",
        string="Upcoming Tender",
        tracking=True,
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Organization",
        related="upcoming_tender_id.partner_id",
        store=True,
        readonly=True,
    )

    tender_title = fields.Char(
        string="Tender Title",
        related="upcoming_tender_id.tender_title",
        store=True,
        readonly=True,
    )

    # ============================================================
    # Sale Orders (one per Working Sheet)
    # ============================================================
    quotation_state = fields.Selection(
    [
        ("not_created", "No Quotation Created"),
        ("partial", "Partially Created"),
        ("created", "All Quotations Created"),
    ],
        string="Quotation Status",
        compute="_compute_quotation_state",
        store=True,
        tracking=True,
    )

    @api.depends("sale_order_ids", "worksheet_ids")
    def _compute_quotation_state(self):
        for rec in self:
            total_worksheets = len(rec.worksheet_ids)
            created = len(rec.sale_order_ids.mapped("worksheet_id"))

            if created == 0:
                rec.quotation_state = "not_created"
            elif created < total_worksheets:
                rec.quotation_state = "partial"
            else:
                rec.quotation_state = "created"
    sale_order_ids = fields.One2many(
        "sale.order",
        "tender_id",
        string="Quotations",
    )

    sale_order_count = fields.Integer(
        string="Quotations Count",
        compute="_compute_sale_order_count",
    )

    @api.depends("sale_order_ids")
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = len(rec.sale_order_ids)

    # def action_create_sale_order(self):
    #     """Open a wizard to let the user specify how many Sale Orders to
    #     create for each Working Sheet."""
    #     self.ensure_one()

    #     if not self.worksheet_ids:
    #         raise ValidationError("No Working Sheets found on this tender.")

    #     line_vals = []
    #     for worksheet in self.worksheet_ids:
    #         existing_count = self.env["sale.order"].search_count([
    #             ("tender_id", "=", self.id),
    #             ("worksheet_id", "=", worksheet.id),
    #         ])
    #         line_vals.append((0, 0, {
    #             "worksheet_id": worksheet.id,
    #             "existing_count": existing_count,
    #             "so_count": 0,
    #         }))

    #     wizard = self.env["tdc.tender.create.so.wizard"].create({
    #         "tender_id": self.id,
    #         "line_ids": line_vals,
    #     })

    #     return {
    #         "type": "ir.actions.act_window",
    #         "name": "Create Sale Orders",
    #         "res_model": "tdc.tender.create.so.wizard",
    #         "view_mode": "form",
    #         "res_id": wizard.id,
    #         "target": "new",
    #     }
    def action_create_sale_order(self):
        
        """Directly create one Sale Order per Working Sheet that doesn't
        already have one — no wizard step, no popup."""
        self.ensure_one()
 
        if not self.worksheet_ids:
            raise ValidationError("No Working Sheets found on this tender.")
 
        gst_tax = self.env["account.tax"].search(
            [("tax_group_id.name", "=", "GST 18%")], limit=1,
        )
 
        created = self.env["sale.order"]
 
        for worksheet in self.worksheet_ids:
            existing_count = self.env["sale.order"].search_count([
                ("tender_id", "=", self.id),
                ("worksheet_id", "=", worksheet.id),
            ])
            if existing_count:
                # Already has a Sale Order — skip it.
                continue
 
            if not worksheet.line_ids:
                raise ValidationError(
                    f"Working Sheet {worksheet.name} has no lines — cannot create Sale Orders."
                )
 
            sale = self.env["sale.order"].create({
                "partner_id": self.upcoming_tender_id.partner_id.id,
                "is_tender_sale": True,
                "tender_id": self.id,
                "upcoming_tender_id": self.upcoming_tender_id.id,
                "worksheet_id": worksheet.id,
            })
 
            for wl in worksheet.line_ids:
                price_unit = wl.unit_cnf_at_site if worksheet.is_cnf else wl.unit_ex_gst_corrected

                if worksheet.is_cnf:
                    tax_ids = [(6, 0, [])]  # duty & transport already included manually, no separate tax
                else:
                    tax_ids = [(6, 0, gst_tax.ids)]

                self.env["sale.order.line"].create({
                    "order_id": sale.id,
                    "product_id": wl.product_id.id,
                    "name": wl.product_id.get_product_multiline_description_sale(),
                    "product_uom_qty": wl.qty,
                    "price_unit": price_unit,
                    "currency_rate": wl.currency_rate,
                    "list_price": wl.list_price,
                    "discount_margin": wl.discount_margin,
                    "net_discount_price": wl.net_discount_price,
                    "tax_ids": tax_ids,
                    "is_cnf": worksheet.is_cnf,
                    "unit_cnf_at_site" : wl.unit_cnf_at_site,
                    "total_cnf_at_site": wl.total_cnf_at_site,
                })
    
                created |= sale
    
        if not created:
            raise ValidationError(
                "No Sale Orders created — every Working Sheet already has one."
            )
 
        if len(created) == 1:
            return {
                "type": "ir.actions.act_window",
                "res_model": "sale.order",
                "view_mode": "form",
                "res_id": created.id,
                "target": "current",
            }
 
        return {
            "type": "ir.actions.act_window",
            "name": "Quotations",
            "res_model": "sale.order",
            "view_mode": "list,form",
            "domain": [("id", "in", created.ids)],
            "target": "current",
        }
    def action_view_sale_order_summary(self):
        """Show all Sale Orders created under this tender."""
        self.ensure_one()

        action = {
            "type": "ir.actions.act_window",
            "name": "Quotations",
            "res_model": "sale.order",
            "domain": [("tender_id", "=", self.id)],
            "context": {"default_tender_id": self.id},
        }

        if self.sale_order_count == 1:
            action.update({
                "view_mode": "form",
                "res_id": self.sale_order_ids.id,
            })
        else:
            action["view_mode"] = "list,form"

        return action
    # ============================================================
    # Tender Fee
    # ============================================================
    tender_fee_amount = fields.Float(string="Tender Fee Amount")

    instrument_type = fields.Selection(
        [
            ("pay_order", "Pay Order"),
            ("cdr", "CDR"),
            ("cash", "Cash"),
            ("challan", "Custom Challan"),
        ],
        string="Instrument Type",
    )

    instrument_id = fields.Many2one("tdc.instruments", string="Instrument Type")

    payment_state = fields.Selection(
        [
            ("not_paid", "Not Paid"),
            ("paid", "Paid"),
        ],
        string="Payment Status",
        default="not_paid",
        tracking=True,
    )

    # ============================================================
    # Accounting
    # ============================================================
    move_id = fields.Many2one("account.move", string="Journal Entry", readonly=True, copy=False)

    journal_entry_count = fields.Integer(compute="_compute_journal_entry_count")

    def _compute_journal_entry_count(self):
        for rec in self:
            rec.journal_entry_count = 1 if rec.move_id else 0

    debit_account_id = fields.Many2one(
        "account.account",
        string="Debit Account",
        default=lambda self: self.env["account.account"].search(
            [("code", "=", "620101")], limit=1,
        ),
        required=True,
    )

    credit_account_id = fields.Many2one(
        "account.account",
        string="Credit Account",
        default=lambda self: self.env["account.account"].search(
            [("code", "=", "101001")], limit=1,
        ),
        required=True,
    )

    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        domain="[('type', 'in', ('bank', 'cash', 'general'))]",
    )

    # ============================================================
    # Payment Method Fields
    # ============================================================
    payment_type = fields.Selection(
        [
            ("pay_order", "Pay Order"),
            ("cdr", "CDR"),
            ("cash", "Cash"),
            ("easypaisa", "EasyPaisa"),
            ("jazzcash", "JazzCash"),
            ("challan", "Custom Challan"),
        ],
        string="Payment Method",
    )

    payment_method_id = fields.Many2one("tdc.payment.method", string="Payment Method")
    in_favour_of = fields.Char(string="Beneficiary")
    bank_name = fields.Char(string="Bank Name")
    account_title = fields.Char(string="Account Title")
    account_number = fields.Char(string="Account Number")

    payment_attachment = fields.Binary(string="Payment Proof", attachment=True)
    payment_attachment_filename = fields.Char(string="Attachment Name")
    payment_note = fields.Text(string="Note")

    attachment_line_ids = fields.One2many(
        "tdc.tender.attachment.line",
        "tender_id",
        string="Payment Attachments",
    )

    def action_add_attachment(self):
        """Add new attachment - max 12"""
        self.ensure_one()
        if len(self.attachment_line_ids) >= 12:
            raise ValidationError("Maximum 12 payment attachments allowed.")

        return self.env["tdc.tender.attachment.line"].create({
            "tender_id": self.id,
        })


    # ============================================================
    # State Management with Approval Workflow
    # ============================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("request_payment", "Request to Tender Fee"),
            ("submitted", "Submitted for Approval"),
            ("approved", "Approved"),
            ("paid", "Paid"),
            ("confirm", "Confirmed"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    submitted_by_id = fields.Many2one("res.users", string="Submitted By", readonly=True, tracking=True)
    submitted_date = fields.Datetime(string="Submitted Date", readonly=True)
    approved_by_id = fields.Many2one("res.users", string="Approved By", readonly=True, tracking=True)
    approval_date = fields.Datetime(string="Approval Date", readonly=True)

    # ============================================================
    # Working Sheets
    # ============================================================
    worksheet_ids = fields.Many2many(
        "tdc.working.sheet",
        relation="tdc_tender_working_sheet_rel",
        column1="tender_id",
        column2="worksheet_id",
        string="Working Sheets",
    )

    project_ids = fields.Many2many(
        "tdc.upcoming.tender",
        string="Projects",
    )

    worksheet_line_ids = fields.Many2many(
        "tdc.working.sheet.line",
        string="Working Sheet Lines",
        compute="_compute_worksheet_line_ids",
        store=False,
    )

    @api.depends("worksheet_ids")
    def _compute_worksheet_line_ids(self):
        for rec in self:
            rec.worksheet_line_ids = rec.worksheet_ids.mapped("line_ids")

    # ============================================================
    # Workflow Methods
    # ============================================================
    def action_request_payment(self):
        for rec in self:
            if rec.tender_fee_amount <= 0:
                raise ValidationError(
                    "Please enter a Tender Fee Amount greater than zero before requesting payment."
                )
        self.write({"state": "request_payment"})

    def action_submit_for_approval(self):
        self.ensure_one()

        if self.state != "request_payment":
            raise ValidationError(
                "You can only submit for approval when in 'Request to Tender Fee' state."
            )

        if not any(line.payment_attachment for line in self.attachment_line_ids):
            raise ValidationError(
                "Please attach payment proof before submitting for approval."
            )

        self.write({
            "state": "submitted",
            "submitted_by_id": self.env.user.id,
            "submitted_date": fields.Datetime.now(),
        })

    def action_approve_payment(self):
        self.ensure_one()

        if self.state != "submitted":
            raise ValidationError(
                "You can only approve when in 'Submitted for Approval' state."
            )

        if not self.env.user.has_group("tdc_tender.group_tender_payment_approver"):
            raise UserError(
                "You don't have permission to approve payments. "
                "Please contact your system administrator."
            )

        self.write({
            "state": "approved",
            "approved_by_id": self.env.user.id,
            "approval_date": fields.Datetime.now(),
        })

    def action_pay(self):
        self.ensure_one()

        if self.state != "approved":
            raise ValidationError("Payment must be approved before marking as paid.")

        if not self.journal_id:
            raise ValidationError("Please select a Payment Journal.")

        if not self.debit_account_id:
            raise ValidationError("Please select a Debit Account.")

        if not self.credit_account_id:
            raise ValidationError("Please select a Credit Account.")

        if self.tender_fee_amount <= 0:
            raise ValidationError("Tender Fee Amount must be greater than zero.")

        move = self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": self.journal_id.id,
            "ref": self.name,
            "line_ids": [
                (0, 0, {
                    "name": self.name,
                    "account_id": self.debit_account_id.id,
                    "debit": self.tender_fee_amount,
                    "credit": 0.0,
                    "partner_id": self.partner_id.id,
                }),
                (0, 0, {
                    "name": self.name,
                    "account_id": self.credit_account_id.id,
                    "debit": 0.0,
                    "credit": self.tender_fee_amount,
                    "partner_id": self.partner_id.id,
                }),
            ],
        })

        move.action_post()

        self.write({
            "move_id": move.id,
            "payment_state": "paid",
            "state": "paid",
        })

        return True

    def action_confirm(self):
        for rec in self:
            # if rec.state != "paid":
            #     raise ValidationError("Payment must be marked as paid before confirming.")

            rec.state = "confirm"

            if rec.upcoming_tender_id:
                rec.upcoming_tender_id.write({
                    "state": "created",
                    "tender_id": rec.id,
                })
    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
        
    def action_view_journal_entries(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Journal Entry",
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": self.move_id.id,
        }

    def action_view_upcoming_tender(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Upcoming Tender",
            "res_model": "tdc.upcoming.tender",
            "view_mode": "form",
            "res_id": self.upcoming_tender_id.id,
            "target": "current",
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                upcoming = self.env["tdc.upcoming.tender"].browse(
                    vals.get("upcoming_tender_id")
                )

                if upcoming and upcoming.name:
                    upcoming_seq = upcoming.name.split("/")[-1]

                    tender_count = self.search_count([
                        ("upcoming_tender_id", "=", upcoming.id)
                    ]) + 1

                    vals["name"] = f"TPR/{upcoming_seq}/Tender/{str(tender_count).zfill(4)}"
                else:
                    vals["name"] = self.env["ir.sequence"].next_by_code(
                        "tdc.tender"
                    ) or "New"

        return super().create(vals_list)


class TDCTenderSaleOrderWizard(models.TransientModel):
    _name = "tdc.tender.sale.order.wizard"
    _description = "Sale Orders Summary per Working Sheet"

    tender_id = fields.Many2one("tdc.tender", string="Tender", readonly=True)
    line_ids = fields.One2many(
        "tdc.tender.sale.order.wizard.line",
        "wizard_id",
        string="Summary",
    )


class TDCTenderSaleOrderWizardLine(models.TransientModel):
    _name = "tdc.tender.sale.order.wizard.line"
    _description = "Sale Order Summary Line"

    wizard_id = fields.Many2one(
        "tdc.tender.sale.order.wizard",
        ondelete="cascade",
    )
    worksheet_id = fields.Many2one(
        "tdc.working.sheet",
        string="Working Sheet",
        readonly=True,
    )
    sale_order_count = fields.Integer(
        string="Sale Orders Created",
        readonly=True,
    )

class TDCTenderCreateSOWizard(models.TransientModel):
    _name = "tdc.tender.create.so.wizard"
    _description = "Create Sale Orders per Working Sheet"

    tender_id = fields.Many2one("tdc.tender", required=True)
    line_ids = fields.One2many(
        "tdc.tender.create.so.wizard.line", "wizard_id", string="Working Sheets"
    )

    def action_confirm(self):
        self.ensure_one()
        Tax = self.env["account.tax"]
        gst_tax = self.env["account.tax"].search(
            [("tax_group_id.name", "=", "GST 18%")], limit=1,
        )
        tender = self.tender_id
        created = self.env["sale.order"]

        for line in self.line_ids:
            if line.so_count <= 0:
                continue

            worksheet = line.worksheet_id

            if not worksheet.line_ids:
                raise ValidationError(
                    f"Working Sheet {worksheet.name} has no lines — cannot create Sale Orders."
                )

            for _ in range(line.so_count):
                sale = self.env["sale.order"].create({
                    "partner_id": tender.upcoming_tender_id.partner_id.id,
                    "is_tender_sale": True,
                    "tender_id": tender.id,
                    "upcoming_tender_id": tender.upcoming_tender_id.id,
                    "worksheet_id": worksheet.id,
                   
                })

                for wl in worksheet.line_ids:
                    price_unit = wl.total_cnf_at_site if worksheet.is_cnf else wl.unit_ex_gst_corrected
                    if worksheet.is_cnf:
                        cnf_taxes = wl.custom_duty_tax_id | wl.local_transport_tax_id
                        tax_ids = [(6, 0, cnf_taxes.ids)]
                    else:
                        tax_ids = [(6, 0, gst_tax.ids)]
                    self.env["sale.order.line"].create({
                        "order_id": sale.id,
                        "product_id": wl.product_id.id,
                        "name": wl.product_id.get_product_multiline_description_sale(),
                        "product_uom_qty": wl.qty,
                        "price_unit": price_unit,
                        "currency_rate": wl.currency_rate,
                        "list_price": wl.list_price,
                        "discount_margin": wl.discount_margin,
                        "net_discount_price": wl.net_discount_price,
                        # "tax_ids": [(6, 0, (cnf_tax_1 | cnf_tax_2).ids)] if worksheet.is_cnf else [(6, 0, gst_tax.ids)],                       
                        "tax_ids": tax_ids,
                        "is_cnf": worksheet.is_cnf,
                        "total_cnf_at_site": wl.total_cnf_at_site,
                    })

                created |= sale

        if not created:
            raise ValidationError(
                "No Sale Orders created — please enter a quantity greater than zero "
                "for at least one Working Sheet."
            )

        if len(created) == 1:
            return {
                "type": "ir.actions.act_window",
                "res_model": "sale.order",
                "view_mode": "form",
                "res_id": created.id,
                "target": "current",
            }

        return {
            "type": "ir.actions.act_window",
            "name": "Quotations",
            "res_model": "sale.order",
            "view_mode": "list,form",
            "domain": [("id", "in", created.ids)],
            "target": "current",
        }


class TDCTenderCreateSOWizardLine(models.TransientModel):
    _name = "tdc.tender.create.so.wizard.line"
    _description = "Working Sheet Sale Order Quantity Line"

    wizard_id = fields.Many2one("tdc.tender.create.so.wizard", ondelete="cascade")
    worksheet_id = fields.Many2one("tdc.working.sheet", readonly=True)
    existing_count = fields.Integer(string="Created", readonly=True)
    so_count = fields.Integer(string="To Be")

    @api.constrains("so_count")
    def _check_so_count(self):
        for rec in self:
            if rec.so_count < 0:
                raise ValidationError("Quantity cannot be negative.")