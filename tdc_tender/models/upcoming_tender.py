from odoo import api, fields, models
from odoo.exceptions import ValidationError

class UpcomingTender(models.Model):
    _name = "tdc.upcoming.tender"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Upcoming Tender"
    _rec_name = "name"
    _order = "id desc"

    name = fields.Char(
        string="Tender Project Ref",
        default="New",
        readonly=True,
        copy=False,
    )

    # organization_id = fields.Many2one(
    #     "res.partner",
    #     string="Organization",
    #     required=True,
    # )

    partner_id = fields.Many2one(
         "res.partner",
         string="Organization",
         required=True,
    )
    priority = fields.Selection(
        [
            ("0", "Low"),
            ("1", "Normal"),
            ("2", "Important"),
        ],
        string="Priority",
        default="1",
        tracking=True,
    )

    tender_title = fields.Char(
        string="Tender Title",
        required=True,
    )
    tender_item = fields.Char(
        string="Tender Item",
        required=True,
    )

    product_line_ids = fields.One2many(
    "tdc.upcoming.tender.line",
    "tender_id",
    string="Products",
    )

    source_id = fields.Many2one(
        "tdc.tender.source",
        string="Source",
    )
    publish_date = fields.Date()

    due_date = fields.Date()

    publish_date_display = fields.Char(
        string='Publish Date',
        compute='_compute_date_display',
    )
    due_date_display = fields.Char(
        string='Due Date',
        compute='_compute_date_display',
    )

    incoterm_id = fields.Many2one(
        'tdc.incoterms', 
        string='Incoterm', 
        help="International Commercial Terms"
    )

    welkin_hitech = fields.Boolean(
        string="Welkin Hitech",
        default=True,
    )
    ather_enterprise = fields.Boolean(
        string="Ather & Sons",
    )

    @api.onchange("welkin_hitech")
    def _onchange_welkin_hitech(self):
        if self.welkin_hitech:
            self.ather_enterprise = False

    @api.onchange("ather_enterprise")
    def _onchange_ather_enterprise(self):
        if self.ather_enterprise:
            self.welkin_hitech = False

    # 2. Selection Field for Tender Stage / Process
    tender_stage = fields.Selection([
        ('single_stage_one_envelope', 'Single Stage One Envelope'), #(TechnoFinancial)
        ('single_stage_two_envelope', 'Single Stage Two Envelope'), # (Technical and Financial)'
        ('double_stage_one_envelope', 'Double Stage One Envelope'), #All Three
        ('double_stage_two_envelope', 'Double Stage Two Envelope'), #All Three
        
    ], string='Tender Process/Stage', default='single_stage_one_envelope')

    # 3. Tender Reference Note
    tender_ref_note = fields.Text(string='Tender Reference Note')

    def _compute_date_display(self):
        for rec in self:
            rec.publish_date_display = rec.publish_date.strftime('%d %b %Y') if rec.publish_date else ''
            rec.due_date_display = rec.due_date.strftime('%d %b %Y') if rec.due_date else ''


    tender_notice = fields.Binary(
        string="Tender Notice",
        attachment=True,
    )

    tender_notice_filename = fields.Char()

    tender_docs = fields.Binary(
        string="Tender Documents",
        attachment=True,
    )

   

    tender_docs_filename = fields.Char()

    remarks = fields.Text()

    not_participated_reason = fields.Selection(
    [
        ("high_security", "High Security Deposit"),
        ("out_of_scope", "Out of Scope"),
        ("low_margin", "Low Profit Margin"),
        ("stock_unavailable", "Stock Unavailable"),
        ("late_notice", "Late Tender Notice"),
        ("documentation", "Documentation Issue"),
        ("technical", "Technical Requirements Not Met"),
        ("other", "Other"),
    ],
    string="Reason",
    )

    not_participated_notes = fields.Text(
        string="Notes",
    )

    state = fields.Selection(
    [
        ("draft", "Draft"),
        ("participated", "In Progress"),
        ("not_participated", "Not Participated"),
        ("created", "Tender Created"),
    ],
    default="draft",
    tracking=True,
        )

    tender_id = fields.Many2one(
        "tdc.tender",
        string="Tender",
        readonly=True,
        copy=False,
    )
    tender_count = fields.Integer(
        string="Tender Count",
        compute="_compute_tender_count",
    )

    def action_view_tender(self):
        self.ensure_one()

        if not self.tender_id:
            return False

        return {
            "type": "ir.actions.act_window",
            "name": "Tender",
            "res_model": "tdc.tender",
            "res_id": self.tender_id.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.depends("tender_id")
    def _compute_tender_count(self):
        for rec in self:
            rec.tender_count = 1 if rec.tender_id else 0
   
    def action_not_participated(self):

        for rec in self:

            if not rec.not_participated_reason:
                raise ValidationError(
                    "Please select a reason before marking the tender as Not Participated."
                )

            rec.state = "not_participated"
    
   

    def action_create_tender(self):
        self.ensure_one()

        worksheets = self.env["tdc.working.sheet"].search([
            ("project_ids", "in", self.id)
        ])

        tender = self.env["tdc.tender"].create({
            "tender_title": self.tender_title,
            "upcoming_tender_id": self.id,
            "worksheet_ids": [(6, 0, worksheets.ids)],
            "project_ids": [(6, 0, worksheets.mapped("project_ids").ids)],
        })

        self.tender_id = tender.id

        return {
            "type": "ir.actions.act_window",
            "res_model": "tdc.tender",
            "res_id": tender.id,
            "view_mode": "form",
            "target": "current",
        }
        
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                dt = fields.Date.to_date(
                    vals.get("publish_date")
                ) or fields.Date.context_today(self)

                seq = self.env["ir.sequence"].next_by_code(
                    "tdc.upcoming.tender"
                ) or "0001"

                vals["name"] = f"TPR/{dt:%m%y}/{seq}"

        return super().create(vals_list)

    def action_participate(self):
        self.state = "participated"