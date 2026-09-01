from odoo import fields, models
from odoo.exceptions import ValidationError, UserError

class TDCSaleEvaluationLine(models.Model):
    _name = "tdc.sale.evaluation.line"
    _description = "Tender Sale Order Evaluation Line"

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        required=True,
        ondelete="cascade",
    )

    stage = fields.Selection(
        [
            ("technical", "Technical Evaluation"),
            ("financial", "Financial Evaluation"),
            ("loa", "Letter of Acceptance"),
        ],
        string="Stage",
        required=True,
    )

    attachment = fields.Binary(string="Attachment", attachment=True)
    attachment_filename = fields.Char(string="Attachment Name")

    name = fields.Char(string="Name")
    notes = fields.Text(string="Notes")
    details = fields.Text(string="Details")

    user_id = fields.Many2one(
        "res.users",
        string="Added By",
        default=lambda self: self.env.user,
        readonly=True,
    )
    date = fields.Date(
        string="Date",
        default=fields.Date.today,
        readonly=True,
    )

class SaleOrder(models.Model):
    _inherit = "sale.order"

    validity_date = fields.Date(string="Validity")
    
    is_tender_sale = fields.Boolean(
        string="Tender Sale",
        readonly=True,
    )

    tender_id = fields.Many2one(
        "tdc.tender",
        string="Tender",
        readonly=True,
    )

    upcoming_tender_id = fields.Many2one(
        "tdc.upcoming.tender",
        string="Upcoming Tender",
        readonly=True,
    )

    tender_title = fields.Char(
        related="upcoming_tender_id.tender_title", readonly=True
    )
    tender_item = fields.Char(
        related="upcoming_tender_id.tender_item", readonly=True
    )
    incoterm_id = fields.Many2one(
        related="upcoming_tender_id.incoterm_id", readonly=True
    )
    incoterm_id = fields.Many2one(
            "tdc.incoterms",
            related="upcoming_tender_id.incoterm_id",
            readonly=True,
        )

    source_id = fields.Many2one(
        "tdc.tender.source",
        related="upcoming_tender_id.source_id",
        readonly=True,
    )
    tender_stage = fields.Selection(
        related="upcoming_tender_id.tender_stage", readonly=True
    )
    tender_ref_note = fields.Text(
        related="upcoming_tender_id.tender_ref_note", readonly=True
    )

    welkin_hitech = fields.Boolean(
        related="upcoming_tender_id.welkin_hitech", readonly=True
    )
    ather_enterprise = fields.Boolean(
        related="upcoming_tender_id.ather_enterprise", readonly=True
    )

    worksheet_id = fields.Many2one(
        "tdc.working.sheet",
        string="Working Sheet",
        readonly=True,
    )

    earnest_money_count = fields.Integer(
        string="Earnest Money Count",
        compute="_compute_earnest_money_count"
    )

    earnest_money_ids = fields.One2many(
        'tdc.earnest.money',
        string="Earnest Money",
        compute="_compute_earnest_money_ids",
        readonly=True,
    )

    def _compute_earnest_money_count(self):
        for rec in self:
            rec.earnest_money_count = self.env['tdc.earnest.money'].search_count([
                ('tender_id', '=', rec.tender_id.id)
            ])

    def _compute_earnest_money_ids(self):
        for rec in self:
            rec.earnest_money_ids = self.env['tdc.earnest.money'].search([
                ('tender_id', '=', rec.tender_id.id)
            ])

    def action_view_earnest_money(self):
        """View earnest money from sale order"""
        self.ensure_one()
        earnest_money = self.env['tdc.earnest.money'].search([
            ('tender_id', '=', self.tender_id.id)
        ])
        
        if earnest_money:
            # If exists, open in form view
            return {
                'type': 'ir.actions.act_window',
                'name': 'Earnest Money',
                'res_model': 'tdc.earnest.money',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': earnest_money.id,  # Open the existing record
                'target': 'current',
            }
        else:
            # If doesn't exist, create new
            return {
                'type': 'ir.actions.act_window',
                'name': 'Create Earnest Money',
                'res_model': 'tdc.earnest.money',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
                'context': {
                    'default_tender_id': self.tender_id.id,
                    'default_upcoming_tender_id': self.upcoming_tender_id.id,
                    'default_validity_date': self.validity_date or fields.Date.today(),
                    'default_quotation_id': self.id,
                }
            }

    def action_create_earnest_money(self):
        """Create earnest money directly"""
        self.ensure_one()
        
        # Check if earnest money already exists
        existing = self.env['tdc.earnest.money'].search([
            ('tender_id', '=', self.tender_id.id)
        ], limit=1)
        
        if existing:
            # If exists, open it
            return {
                'type': 'ir.actions.act_window',
                'name': 'Earnest Money',
                'res_model': 'tdc.earnest.money',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': existing.id,
                'target': 'current',
            }
        
        # Create new earnest money (only if none exists)
        earnest_money = self.env['tdc.earnest.money'].create({
            'tender_id': self.tender_id.id,
            'upcoming_tender_id': self.upcoming_tender_id.id,
            'validity_date': self.validity_date or fields.Date.today(),
            'quotation_id': self.id,   # <-- added
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Earnest Money',
            'res_model': 'tdc.earnest.money',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': earnest_money.id,
            'target': 'current',
        }

    # ------------- perfomance bond --------------


     # Performance Bond fields
    performance_bond_count = fields.Integer(
        string="Performance Bond Count",
        compute="_compute_performance_bond_count"
    )

    performance_bond_ids = fields.One2many(
        'tdc.performance.bond',
        string="Performance Bond",
        compute="_compute_performance_bond_ids",
        readonly=True,
    )

    # Check if order is delivered
    is_delivered = fields.Boolean(
        string="Is Delivered",
        compute="_compute_is_delivered",
        store=True,
    )

    def _compute_is_delivered(self):
            

        for rec in self:
            delivered = True
            if rec.picking_ids:
                for picking in rec.picking_ids:
                    if picking.state != 'done':
                        delivered = False
                        break
            else:
                delivered = False
            rec.is_delivered = delivered

    def _compute_performance_bond_count(self):
        for rec in self:
            rec.performance_bond_count = self.env['tdc.performance.bond'].search_count([
                ('sale_order_id', '=', rec.id)
            ])

    def _compute_performance_bond_ids(self):
        for rec in self:
            rec.performance_bond_ids = self.env['tdc.performance.bond'].search([
                ('sale_order_id', '=', rec.id)
            ])

    def action_view_performance_bond(self):
        """View performance bond from sale order"""
        self.ensure_one()
        performance_bond = self.env['tdc.performance.bond'].search([
            ('sale_order_id', '=', self.id)
        ])
        
        if performance_bond:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Performance Bond',
                'res_model': 'tdc.performance.bond',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': performance_bond.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Create Performance Bond',
                'res_model': 'tdc.performance.bond',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
                'context': {
                    'default_tender_id': self.tender_id.id,
                    'default_upcoming_tender_id': self.upcoming_tender_id.id,
                    'default_sale_order_id': self.id,
                    'default_quotation_date': self.date_order or fields.Date.today(),
                    'default_delivery_date': fields.Date.today(),
                }
            }

    def action_create_performance_bond(self):
        """Create performance bond directly"""
        self.ensure_one()
        
        # Check if already exists
        existing = self.env['tdc.performance.bond'].search([
            ('sale_order_id', '=', self.id)
        ], limit=1)
        
        if existing:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Performance Bond',
                'res_model': 'tdc.performance.bond',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': existing.id,
                'target': 'current',
            }
        
        # Get delivery date from stock.picking schedule date
        delivery_date = fields.Date.today()
        if self.picking_ids:
            # Get the last done picking or any picking with schedule date
            done_pickings = self.picking_ids.filtered(lambda p: p.state == 'done')
            if done_pickings:
                # Use the schedule date from the last done picking
                last_picking = done_pickings.sorted('date_done', reverse=True)[0]
                delivery_date = last_picking.scheduled_date.date() if last_picking.scheduled_date else fields.Date.today()
            else:
                # If no done picking, use schedule date from any picking
                first_picking = self.picking_ids.sorted('date', reverse=True)[0]
                delivery_date = first_picking.scheduled_date.date() if first_picking.scheduled_date else fields.Date.today()
        
        # Create new performance bond
        performance_bond = self.env['tdc.performance.bond'].create({
            'tender_id': self.tender_id.id,
            'upcoming_tender_id': self.upcoming_tender_id.id,
            'sale_order_id': self.id,
            'quotation_date': self.date_order or fields.Date.today(),
            'delivery_date': delivery_date,  # Now from stock.picking scheduled_date
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Performance Bond',
            'res_model': 'tdc.performance.bond',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': performance_bond.id,
            'target': 'current',
        }

        

    # ----------- perofmane bond end -------------
    def action_view_working_sheet(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Working Sheet",
            "res_model": "tdc.working.sheet",
            "view_mode": "form",
            "res_id": self.worksheet_id.id,
            "target": "current",
        }
    
    def action_print_technical_quotation(self):
        self.ensure_one()

        return self.env.ref(
            "tdc_tender.action_report_technical_quotation"
        ).report_action(self.tender_id)

    def action_print_financial_quotation(self):
        self.ensure_one()
        return self.env.ref(
            "tdc_tender.action_report_financial_quotation"
        ).report_action(self)


    def action_print_techno_financial_quotation(self):
        self.ensure_one()
        return self.env.ref(
            "tdc_tender.action_report_techno_financial_quotation"
        ).report_action(self)

    technical_terms = fields.Html(
        string="Technical Quotation Terms & Conditions",
    )

    financial_terms = fields.Html(
        string="Financial Quotation Terms & Conditions",
    )

    techno_financial_terms = fields.Html(
        string="Techno Financial Terms & Conditions",
    )


    tender_workflow_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submit_tender", "Submit Tender"),
            ("technical_evaluation", "Technical Evaluation"),
            ("financial_evaluation", "Financial Evaluation"),
            ("letter_of_acceptance", "Letter of Acceptance"),
            ("confirmed", "Confirmed"),
            ("closed", "Closed"),
        ],
        string="Tender Stage",
        default="draft",
        tracking=True,
        copy=False,
    )

    technical_evaluation_line_ids = fields.One2many(
        "tdc.sale.evaluation.line",
        "sale_order_id",
        string="Technical Evaluation",
        domain=[("stage", "=", "technical")],
    )
    financial_evaluation_line_ids = fields.One2many(
        "tdc.sale.evaluation.line",
        "sale_order_id",
        string="Financial Evaluation",
        domain=[("stage", "=", "financial")],
    )
    loa_line_ids = fields.One2many(
        "tdc.sale.evaluation.line",
        "sale_order_id",
        string="Letter of Acceptance",
        domain=[("stage", "=", "loa")],
    )

    def action_close_tender(self):
        self.ensure_one()

        if self.tender_workflow_state == "closed":
            return

        self.tender_workflow_state = "closed"


    def action_submit_tender(self):
        self.ensure_one()

        if self.tender_workflow_state != "draft":
            raise UserError("Tender can only be submitted from Draft.")

        self._get_tender_sibling_orders().write({
            'tender_workflow_state': 'submit_tender',
        })


    def action_start_technical_evaluation(self):
        self.ensure_one()

        if self.tender_workflow_state != "submit_tender":
            raise UserError("Tender must be submitted before technical evaluation.")

        self._get_tender_sibling_orders().write({
            'tender_workflow_state': 'technical_evaluation',
        })


    def action_start_financial_evaluation(self):
        self.ensure_one()

        if self.tender_workflow_state != "technical_evaluation":
            raise UserError("Complete technical evaluation first.")

        if not self.technical_evaluation_line_ids:
            raise UserError(
                "Add at least one technical evaluation line before proceeding."
            )

        self._get_tender_sibling_orders().write({
            'tender_workflow_state': 'financial_evaluation',
        })


    def action_start_letter_of_acceptance(self):
        self.ensure_one()

        if self.tender_workflow_state != "financial_evaluation":
            raise UserError("Complete financial evaluation first.")

        if not self.financial_evaluation_line_ids:
            raise UserError(
                "Add at least one financial evaluation line before proceeding."
            )

        self._get_tender_sibling_orders().write({
            'tender_workflow_state': 'letter_of_acceptance',
        })


    def action_confirm_tender_sale(self):
        self.ensure_one()

        if self.tender_workflow_state != "letter_of_acceptance":
            raise UserError(
                "Letter of Acceptance must be completed before confirming."
            )

        if not self.loa_line_ids:
            raise UserError(
                "Add at least one Letter of Acceptance line before confirming."
            )

        # Yahin se sync khatam — is order ki state ab independent hai,
        # baqi sibling orders 'letter_of_acceptance' me hi rehte hain
        # jab tak wo khud confirm na hon.
        self.tender_workflow_state = "confirmed"

        return self.action_confirm()
    #######################
    def action_open_create_loa_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Create More LOA",
            "res_model": "tdc.create.loa.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_sale_order_id": self.id},
        }

    ##########################################
    def _get_tender_sibling_orders(self):
        """Same tender_id wale sab tender-sale orders (including self)
        jo abhi tak 'confirmed' ya 'closed' nahi hue — inhi ko hum sync
        karte hain jab tak Letter of Acceptance stage tak pohonchte hain."""
        self.ensure_one()
        if not self.tender_id:
            return self
        return self.search([
            ('tender_id', '=', self.tender_id.id),
            ('is_tender_sale', '=', True),
            ('tender_workflow_state', 'not in', ('confirmed', 'closed')),
        ])