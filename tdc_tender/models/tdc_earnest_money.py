from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError

class TDCEarnestMoneyAttachmentLine(models.Model):
    _name = 'tdc.earnest.money.attachment.line'
    _description = 'Earnest Money Attachment Line'

    earnest_money_id = fields.Many2one(
        'tdc.earnest.money',
        string='Earnest Money',
        required=True,
        # ondelete='cascade'
    )
    attachment_stage = fields.Selection(
        [
            ('payment', 'Payment Proof'),
            ('bank_review', 'Bank Return Receiving'),
            ('confirmation', 'Bank Return Confirmation'),
        ],
        string="Attachment Stage",
        default='payment',
        required=True,
    )


    
    # Payment attachment fields
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


# ============================================================
# MAIN EARNEST MONEY MODEL
# ============================================================
class TDCEarnestMoney(models.Model):
    _name = "tdc.earnest.money"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Earnest Money"
    _order = "id desc"

    # ============================================================
    # Name/Reference Fields
    # ============================================================
    name = fields.Char(
        string="Earnest Money Ref",
        required=True,
        copy=False,
        readonly=True,
        default="New",
    )

    is_create_earnest_money = fields.Boolean(
        string="Created via Quick Action",
        default=False,
    )

    # ============================================================
    # Two References to Tenders
    # ============================================================
    upcoming_tender_id = fields.Many2one(
        "tdc.upcoming.tender",
        string="Upcoming Tender",
        
        tracking=True,
    )

    tender_id = fields.Many2one(
        "tdc.tender",
        string="Tender",
        required=True,
        tracking=True,
    )
    @api.onchange('tender_id')
    def _onchange_tender_id(self):
        """Auto-fill upcoming_tender_id when tender_id is selected"""
        if self.tender_id:
            self.upcoming_tender_id = self.tender_id.upcoming_tender_id
            # Reset quotation if it doesn't belong to the new tender
            if self.quotation_id and self.quotation_id.tender_id != self.tender_id:
                self.quotation_id = False

    # ============================================================
    # Tender Information (Related Fields)
    # ============================================================
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

    tender_no = fields.Char(
        string="Tender No.",
        related="tender_id.name",
        store=True,
        readonly=True,
    )

    # ============================================================
    # Quotation Information
    # ============================================================
    quotation_id = fields.Many2one(
    "sale.order",
    string="Quotation",
    domain="[('tender_id', '=', tender_id)]",
    )

    quotation_amount = fields.Float(
        string="Quotation Amount",
        compute="_compute_quotation_amount",
        store=True,
        readonly=True,
    )

    quotation_validity_date = fields.Date(
        string="Quotation Validity Date",
        compute="_compute_quotation_validity",
        store=True,
        readonly=True,
    )

    @api.depends('quotation_id', 'quotation_id.amount_total')
    def _compute_quotation_amount(self):
        for rec in self:
            rec.quotation_amount = rec.quotation_id.amount_total if rec.quotation_id else 0.0

    @api.depends('quotation_id', 'quotation_id.validity_date')
    def _compute_quotation_validity(self):
        for rec in self:
            rec.quotation_validity_date = rec.quotation_id.validity_date if rec.quotation_id else False

    # ============================================================
    # Earnest Money Amount Fields
    # ============================================================
    amount_calculation_type = fields.Selection(
        [
            ('percentage', 'Percentage of Quotation'),
            ('fixed', 'Fixed Amount'),
        ],
        string="Amount Calculation Type",
        default='percentage',
        tracking=True,
    )

    percentage_value = fields.Float(
        string="Percentage (%)",
        tracking=True,
    )

    earnest_money_amount = fields.Float(
        string="Earnest Money Amount",
        tracking=True,
    )

    @api.onchange('amount_calculation_type', 'percentage_value', 'quotation_amount')
    def _onchange_calculate_amount(self):
        """Auto-calculate earnest money amount based on selection"""
        if self.amount_calculation_type == 'percentage' and self.quotation_amount > 0:
            self.earnest_money_amount = (self.quotation_amount * self.percentage_value) / 100
        elif self.amount_calculation_type == 'fixed':
            # Keep manual entry, don't override
            pass

    # ============================================================
    # Beneficiary and Remarks
    # ============================================================
    beneficiary = fields.Char(
        string="Beneficiary",
        tracking=True,
    )

    note_remarks = fields.Text(
        string="Note & Remarks",
        tracking=True,
    )

    # ============================================================
    # Date Fields (Validity & Return)
    # ============================================================
    validity_date = fields.Date(
        string="Validity Date",
        tracking=True,
    )

    return_date = fields.Date(
        string="Return Date",
        tracking=True,
    )
    is_validity_expiring = fields.Boolean(
        string="Validity Expiring Soon",
        compute="_compute_is_validity_expiring",
    )

    @api.depends('validity_date')
    def _compute_is_validity_expiring(self):
        """True jab validity_date mein sirf 1 din (ya kam) reh jaye"""
        today = fields.Date.today()
        for rec in self:
            if rec.validity_date:
                remaining_days = (rec.validity_date - today).days
                rec.is_validity_expiring = remaining_days <= 1
            else:
                rec.is_validity_expiring = False

    # Extended Validity Tracking
    is_extended = fields.Boolean(
        string="Is Extended?",
        default=False,
        tracking=True,
    )

    previous_validity_date = fields.Date(
        string="Previous Validity Date",
        readonly=True,
    )

    extension_days = fields.Integer(
        string="Days Extended",
        compute="_compute_extension_days",
        store=True,
    )

    extension_notification = fields.Text(
        string="Extension Notification",
        tracking=True,
    )

    @api.depends('validity_date', 'previous_validity_date')
    def _compute_extension_days(self):
        for rec in self:
            if rec.previous_validity_date and rec.validity_date:
                delta = rec.validity_date - rec.previous_validity_date
                rec.extension_days = delta.days
            else:
                rec.extension_days = 0

    def action_extend_validity(self):
        """Extend validity date with notification"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Extend Validity Date',
            'res_model': 'tdc.earnest.money.extend.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_earnest_money_id': self.id,
                'default_current_validity': self.validity_date,
            }
        }

    # ============================================================
    # Payment Method Fields
    # ============================================================
    payment_type = fields.Selection(
        [
            ('pay_order', 'Pay Order'),
            ('cdr', 'CDR'),
            ('cash', 'Cash'),
            ('easypaisa', 'EasyPaisa'),
            ('jazzcash', 'JazzCash'),
            ('challan', 'Custom Challan'),
            ('bank_guarantee', 'Bank Guarantee'),
        ],
        string="Payment Method",
        tracking=True,
    )

    in_favour_of = fields.Char(
        string="In Favour Of",
        tracking=True,
    )

    bank_name = fields.Char(
        string="Bank Name",
        tracking=True,
    )

    account_title = fields.Char(
        string="Account Title",
        tracking=True,
    )

    account_number = fields.Char(
        string="Account Number",
        tracking=True,
    )

    payment_note = fields.Text(
        string="Payment Note",
        tracking=True,
    )

    # ============================================================
    # Attachments (Max 12)
    # ============================================================
    attachment_line_ids = fields.One2many(
        'tdc.earnest.money.attachment.line',
        'earnest_money_id',
        string='Payment Attachments'
    )

    def action_add_attachment(self):
        """Add new attachment - max 12"""
        self.ensure_one()
        if len(self.attachment_line_ids) >= 12:
            raise ValidationError("Maximum 12 payment attachments allowed.")
        
        return self.env['tdc.earnest.money.attachment.line'].create({
            'earnest_money_id': self.id,
        })

    # ============================================================
    # Payment Status
    # ============================================================
    payment_state = fields.Selection(
        [
            ("not_paid", "Not Paid"),
            ("paid", "Paid"),
            ("returned", "Returned"),
        ],
        string="Payment Status",
        default="not_paid",
        tracking=True,
    )

    # ============================================================
    # Accounting Entries
    # ============================================================
    move_id = fields.Many2one(
        "account.move",
        string="Journal Entry",
        readonly=True,
        copy=False,
    )

    return_move_id = fields.Many2one(
        "account.move",
        string="Return Journal Entry",
        readonly=True,
        copy=False,
    )

    journal_entry_count = fields.Integer(
        compute="_compute_journal_entry_count"
    )

    def _compute_journal_entry_count(self):
        for rec in self:
            count = 0
            if rec.move_id:
                count += 1
            if rec.return_move_id:
                count += 1
            rec.journal_entry_count = count

    debit_account_id = fields.Many2one(
        "account.account",
        string="Debit Account",
        default=lambda self: self.env["account.account"].search(
            [("code", "=", "620101")],
            limit=1,
        ),
        required=True,
    )

    credit_account_id = fields.Many2one(
        "account.account",
        string="Credit Account",
        default=lambda self: self.env["account.account"].search(
            [("code", "=", "101001")],
            limit=1,
        ),
        required=True,
    )

    return_debit_account_id = fields.Many2one(
        "account.account",
        string="Return Debit Account",
        default=lambda self: self.env["account.account"].search(
            [("code", "=", "101001")],
            limit=1,
        ),
    )

    return_credit_account_id = fields.Many2one(
        "account.account",
        string="Return Credit Account",
        default=lambda self: self.env["account.account"].search(
            [("code", "=", "620101")],
            limit=1,
        ),
    )

    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        domain="[('type', 'in', ('bank', 'cash', 'general'))]",
    )
    # Add this field in TDCEarnestMoney class
    return_journal_id = fields.Many2one(
        "account.journal",
        string="Return Journal",
        domain="[('type', 'in', ('bank', 'cash', 'general'))]",
        readonly=True,
    )

    # ============================================================
    # State Management with Approval Workflow
    # ============================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("request_payment", "Request Payment"),
            ("submitted", "Submitted for Approval"),
            ("approved", "Approved"),
            ("paid", "Paid"),
            ("return_requested", "Return Requested"),
            ("return_approved", "Return Approved"),
            ("under_bank_review", "Under Bank Review"),
            ("returned", "Returned"),
            # ("confirm", "Confirmed"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    # Return workflow tracking
    return_requested_by_id = fields.Many2one("res.users", string="Return Requested By", readonly=True)
    return_requested_date = fields.Datetime(string="Return Requested Date", readonly=True)
    return_approved_by_id = fields.Many2one("res.users", string="Return Approved By", readonly=True)
    return_approved_date = fields.Datetime(string="Return Approval Date", readonly=True)
    bank_review_by_id = fields.Many2one("res.users", string="Sent for Bank Review By", readonly=True)
    bank_review_date = fields.Datetime(string="Bank Review Date", readonly=True)

    # Approval Tracking Fields
    submitted_by_id = fields.Many2one(
        "res.users",
        string="Submitted By",
        readonly=True,
        tracking=True,
    )

    submitted_date = fields.Datetime(
        string="Submitted Date",
        readonly=True,
    )

    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        readonly=True,
        tracking=True,
    )

    approval_date = fields.Datetime(
        string="Approval Date",
        readonly=True,
    )

    # ============================================================
    # Workflow Methods
    # ============================================================
    def action_request_payment(self):
        """Step 1: Request payment"""
        # for rec in self:
        #     if rec.earnest_money_amount <= 0:
        #         raise ValidationError(
        #             "Please enter an Earnest Money Amount greater than zero before requesting payment."
        #         )
        self.write({
            "state": "request_payment",
        })

    def action_submit_for_approval(self):
        """Step 2: Submit for approval"""
        self.ensure_one()
        
        if self.state != 'request_payment':
            raise ValidationError(
                "You can only submit for approval when in 'Request Payment' state."
            )
        
        self.write({
            "state": "submitted",
            "submitted_by_id": self.env.user.id,
            "submitted_date": fields.Datetime.now(),
        })

    def action_approve_payment(self):
        """Step 3: Approve payment (Only for users with approver rights)"""
        self.ensure_one()
        
        if self.state != 'submitted':
            raise ValidationError(
                "You can only approve when in 'Submitted for Approval' state."
            )
        
        # Check if user has approval rights
        if not self.env.user.has_group('tdc_tender.group_tender_payment_approver'):
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
        """Step 4: Mark as paid and create accounting entry"""
        self.ensure_one()

        if self.state != 'approved':
            raise ValidationError(
                "Payment must be approved before marking as paid."
            )

        if not self.journal_id:
            raise ValidationError("Please select a Payment Journal.")

        if not self.debit_account_id:
            raise ValidationError("Please select a Debit Account.")

        if not self.credit_account_id:
            raise ValidationError("Please select a Credit Account.")

        if self.earnest_money_amount <= 0:
            raise ValidationError("Earnest Money Amount must be greater than zero.")
                  
        if not any(line.payment_attachment for line in self.attachment_line_ids):
            raise ValidationError(
                "Please attach payment proof before submitting for approval."
            )
        # Create accounting entry
        move = self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": self.journal_id.id,
            "ref": self.name,
            "line_ids": [
                (0, 0, {
                    "name": f"Earnest Money - {self.name}",
                    "account_id": self.debit_account_id.id,
                    "debit": self.earnest_money_amount,
                    "credit": 0.0,
                    "partner_id": self.partner_id.id,
                }),
                (0, 0, {
                    "name": f"Earnest Money - {self.name}",
                    "account_id": self.credit_account_id.id,
                    "debit": 0.0,
                    "credit": self.earnest_money_amount,
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

    def action_request_return(self):
        """Step 5a: Request Return — Paid -> Return Requested"""
        self.ensure_one()
        if self.state != 'paid':
            raise ValidationError("Payment must be marked as paid before requesting return.")
        if self.return_move_id:
            raise ValidationError("This earnest money has already been returned.")
        self.write({
            "state": "return_requested",
            "return_requested_by_id": self.env.user.id,
            "return_requested_date": fields.Datetime.now(),
        })

    def action_approve_return(self):
        """Step 5b: Return Requested -> Return Approved
        NOTE: no approver group check yet — will restrict later."""
        self.ensure_one()
        if self.state != 'return_requested':
            raise ValidationError(
                "You can only approve a return from 'Return Requested' state."
            )
        self.write({
            "state": "return_approved",
            "return_approved_by_id": self.env.user.id,
            "return_approved_date": fields.Datetime.now(),
        })

    def action_send_for_bank_review(self):
        """Step 5c: Return Approved -> Under Bank Review, requires bank receiving proof"""
        self.ensure_one()
        if self.state != 'return_approved':
            raise ValidationError(
                "You can only send for bank review from 'Return Approved' state."
            )
        if not any(
            line.attachment_stage == 'bank_review' and line.payment_attachment
            for line in self.attachment_line_ids
        ):
            raise ValidationError(
                "Please attach the bank receiving proof before sending for bank review."
            )
        self.write({
            "state": "under_bank_review",
            "bank_review_by_id": self.env.user.id,
            "bank_review_date": fields.Datetime.now(),
        })

    def action_return_payment(self):
        """Step 5c: Under Bank Review -> open wizard, requires confirmation attachment"""
        self.ensure_one()
        if self.state != 'under_bank_review':
            raise ValidationError(
                "Return can only be confirmed from 'Under Bank Review' state."
            )
        if not any(
            line.attachment_stage == 'confirmation' and line.payment_attachment
            for line in self.attachment_line_ids
        ):
            raise ValidationError(
                "Please attach the bank confirmation receipt before confirming the return."
            )
        if self.return_move_id:
            raise ValidationError("This earnest money has already been returned.")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Return Earnest Money',
            'res_model': 'tdc.earnest.money.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_earnest_money_id': self.id,
                'default_return_amount': self.earnest_money_amount,
                'default_return_journal_id': self.journal_id.id,
                'default_return_debit_account_id': self.return_debit_account_id.id or self.credit_account_id.id,
                'default_return_credit_account_id': self.return_credit_account_id.id or self.debit_account_id.id,
            }
        }
    # def action_confirm(self):
    #     """Step 6: Final confirmation"""
    #     for rec in self:
    #         if rec.state != 'paid' and rec.state != 'returned':
    #             raise ValidationError(
    #                 "Earnest Money must be paid or returned before confirming."
    #             )
            
    #         rec.state = "confirm"

    def action_view_journal_entries(self):
        """View the journal entries"""
        self.ensure_one()
        
        # Get both journal entries
        moves = []
        if self.move_id:
            moves.append(self.move_id.id)
        if self.return_move_id:
            moves.append(self.return_move_id.id)

        return {
            "type": "ir.actions.act_window",
            "name": "Journal Entries",
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [('id', 'in', moves)],
            "target": "current",
        }

    def action_view_tender(self):
        """View the related tender"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Tender",
            "res_model": "tdc.tender",
            "view_mode": "form",
            "res_id": self.tender_id.id,
            "target": "current",
        }

    # ============================================================
    # Sequence Generation
    # ============================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                # Get the next sequence number
                seq = self.env["ir.sequence"].next_by_code("tdc.earnest.money") or "New"
                vals["name"] = seq
        return super().create(vals_list)

# ============================================================
# WIZARD FOR EXTENDING VALIDITY DATE
# ============================================================
class TDCEarnestMoneyExtendWizard(models.TransientModel):
    _name = 'tdc.earnest.money.extend.wizard'
    _description = 'Extend Earnest Money Validity Wizard'

    earnest_money_id = fields.Many2one(
        'tdc.earnest.money',
        string='Earnest Money',
        required=True,
    )

    current_validity = fields.Date(
        string='Current Validity Date',
        readonly=True,
    )

    new_validity_date = fields.Date(
        string='New Validity Date',
        required=True,
    )

    extension_notification = fields.Text(
        string='Extension Notification',
        required=True,
    )

    def action_extend(self):
        """Extend the validity date"""
        self.ensure_one()
        
        if not self.new_validity_date:
            raise ValidationError("Please select a new validity date.")
        
        if self.current_validity and self.new_validity_date <= self.current_validity:
            raise ValidationError("New validity date must be after current validity date.")
        
        earnest_money = self.earnest_money_id
        earnest_money.write({
            'previous_validity_date': earnest_money.validity_date,
            'validity_date': self.new_validity_date,
            'is_extended': True,
            'extension_notification': self.extension_notification,
        })
        
        return {'type': 'ir.actions.act_window_close'}


# ============================================================
# WIZARD FOR RETURNING EARNEST MONEY
# ============================================================


    

class TDCEarnestMoneyReturnWizard(models.TransientModel):
    _name = 'tdc.earnest.money.return.wizard'
    _description = 'Return Earnest Money Wizard'

    earnest_money_id = fields.Many2one(
        'tdc.earnest.money',
        string='Earnest Money',
        required=True,
    )

    return_amount = fields.Float(
        string='Return Amount',
        required=True,
    )

    return_note = fields.Text(
        string='Return Note',
        required=True,
    )

    # Return Journal Entry Fields
    return_journal_id = fields.Many2one(
        "account.journal",
        string="Return Journal",
        domain="[('type', 'in', ('bank', 'cash', 'general'))]",
        required=True,
    )

    return_debit_account_id = fields.Many2one(
        "account.account",
        string="Return Debit Account",
        required=True,
    )

    return_credit_account_id = fields.Many2one(
        "account.account",
        string="Return Credit Account",
        required=True,
    )

    # Additional attachments for return
    return_attachment = fields.Binary(
        string="Return Attachment",
        attachment=True,
    )
    return_attachment_filename = fields.Char(
        string="Attachment Name"
    )

    def action_confirm_return(self):
        """Confirm return and create reverse journal entry"""
        self.ensure_one()
        
        if self.return_amount <= 0:
            raise ValidationError("Return amount must be greater than zero.")
        
        # Create reverse journal entry
        return_move = self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": self.return_journal_id.id,
            "ref": f"Return - {self.earnest_money_id.name}",
            "date": fields.Date.today(),
            "line_ids": [
                (0, 0, {
                    "name": f"Return Earnest Money - {self.earnest_money_id.name} - {self.return_note or ''}",
                    "account_id": self.return_debit_account_id.id,
                    "debit": self.return_amount,
                    "credit": 0.0,
                    "partner_id": self.earnest_money_id.partner_id.id,
                }),
                (0, 0, {
                    "name": f"Return Earnest Money - {self.earnest_money_id.name} - {self.return_note or ''}",
                    "account_id": self.return_credit_account_id.id,
                    "debit": 0.0,
                    "credit": self.return_amount,
                    "partner_id": self.earnest_money_id.partner_id.id,
                }),
            ],
        })

        return_move.action_post()

        # Update earnest money record
        self.earnest_money_id.write({
            "return_move_id": return_move.id,
            "return_journal_id": self.return_journal_id.id,
            "return_debit_account_id": self.return_debit_account_id.id,
            "return_credit_account_id": self.return_credit_account_id.id,
            "payment_state": "returned",
            "state": "returned",
            "note_remarks": self.return_note,
            "return_date": fields.Date.today(),
        })
        
        return {'type': 'ir.actions.act_window_close'}

class TDCEarnestMoneyExtendWizard(models.TransientModel):
    _name = 'tdc.earnest.money.extend.wizard'
    _description = 'Extend Earnest Money Validity Wizard'

    earnest_money_id = fields.Many2one(
        'tdc.earnest.money',
        string='Earnest Money',
        required=True,
    )

    current_validity = fields.Date(
        string='Current Validity Date',
        readonly=True,
    )

    new_validity_date = fields.Date(
        string='New Validity Date',
        required=True,
    )

    extension_notification = fields.Text(
        string='Extension Notification',
        required=True,
    )

    def action_extend(self):
        """Extend the validity date"""
        self.ensure_one()
        
        if not self.new_validity_date:
            raise ValidationError("Please select a new validity date.")
        
        if self.current_validity and self.new_validity_date <= self.current_validity:
            raise ValidationError("New validity date must be after current validity date.")
        
        earnest_money = self.earnest_money_id
        earnest_money.write({
            'previous_validity_date': earnest_money.validity_date,
            'validity_date': self.new_validity_date,
            'is_extended': True,
            'extension_notification': self.extension_notification,
        })
        
        return {'type': 'ir.actions.act_window_close'}