from odoo import api, fields, models


class TenderWorkingSheet(models.Model):
    _name = "tdc.working.sheet"
    _description = "Tender Working Sheet"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"
    _order = "id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        default="New",
    )

    # tender_ids = fields.One2many(
    #     "tdc.tender",
    #     "worksheet_id",
    #     string="Tenders",
    # )

    tender_ids = fields.Many2many(
        "tdc.tender",
        relation="tdc_tender_working_sheet_rel",
        column1="worksheet_id",
        column2="tender_id",
        string="Tenders",
    )
    
    # delete it by insha
    project_id = fields.Many2one(
        "tdc.upcoming.tender",
        string="Project",
        tracking=True,
    )
    # delete it by insha

    project_ids = fields.Many2many(
        "tdc.upcoming.tender",
        string="Project",
        required=True,
        tracking=True,
    )

    tender_titles = fields.Char(
    string="Tender Title",
    compute="_compute_tender_project_data",
    store=True,
    )

    tender_items = fields.Char(
        string="Tender Item",
        compute="_compute_tender_project_data",
        store=True,
    )

    incoterm_id = fields.Many2one(
        "tdc.incoterms",
        string="Incoterm",
        compute="_compute_tender_project_data",
        store=True,
        readonly=True,
    )

    is_cnf = fields.Boolean(
        string="C&F",
        default=False,
    )
    
    @api.depends("project_ids", "project_ids.tender_title", "project_ids.tender_item", "project_ids.incoterm_id",)
    def _compute_tender_project_data(self):
        for record in self:
            projects = record.project_ids

            record.tender_titles = ", ".join(
                record.project_ids.mapped("tender_title")
            )

            record.tender_items = ", ".join(
                record.project_ids.mapped("tender_item")
            )

            # Incoterm from Upcoming Tender
            if projects:
                record.incoterm_id = projects[0].incoterm_id
            else:
                record.incoterm_id = False


    date = fields.Date(
        string="Date",
        default=fields.Date.context_today,
    )

    line_ids = fields.One2many(
        "tdc.working.sheet.line",
        "sheet_id",
        string="Working Sheet Lines",
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        tracking=True,
    )

    currency_rate = fields.Float(
        string="Currency Rate",
        default=1.0,
        tracking=True,
    )

    @api.onchange('currency_rate')
    def _onchange_currency_rate(self):
        for line in self.line_ids:
            if not line.custom_currency_rate:
                line.currency_rate = self.currency_rate
                
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "tdc.working.sheet"
                ) or "New"

        return super().create(vals_list)


class TenderWorkingSheetLine(models.Model):
    _name = "tdc.working.sheet.line"
    _description = "Tender Working Sheet Line"
    _order = "sequence"

    sheet_id = fields.Many2one(
        "tdc.working.sheet",
        # ondelete="cascade",
    )

    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Sale Order Line',
    )

    sequence = fields.Integer(
        string = "SNo" , 
        readonly=True,
    )

    

    @api.model_create_multi
    def create(self, vals_list):
        sheet_sequences = {}

        for vals in vals_list:
            sheet_id = vals.get("sheet_id")

            if sheet_id and not vals.get("sequence"):
                if sheet_id not in sheet_sequences:
                    last_line = self.search(
                        [("sheet_id", "=", sheet_id)],
                        order="sequence desc",
                        limit=1,
                    )
                    sheet_sequences[sheet_id] = last_line.sequence or 0

                sheet_sequences[sheet_id] += 1
                vals["sequence"] = sheet_sequences[sheet_id]

        records = super().create(vals_list)

        # Resequence ALL lines of each affected sheet, not just the new batch
        sheets = records.mapped("sheet_id")
        for sheet in sheets:
            sheet.line_ids._resequence()

        return records


    def unlink(self):
        sheets = self.mapped("sheet_id")

        res = super().unlink()

        for sheet in sheets:
            sheet.line_ids._resequence()

        return res


    def _resequence(self):
        seq = 1

        for line in self.sorted("sequence"):
            line.sequence = seq
            seq += 1

    qty = fields.Float(
        string="Qty",
        default=1,
    )

    product_id = fields.Many2one(
        "product.product",
        string="Item",
        required=True,
    )

    model = fields.Char(
        string="Model Quoted",
        related="product_id.product_tmpl_id.tender_model",
        store=True,
    )
    model_no_id = fields.Many2one(
        "product.model",
        string="Model No",
        related="product_id.product_tmpl_id.model_no_id",
        store=True,
        readonly=True,
    )
    custom_currency_rate = fields.Boolean(
        string="Custom Rate",
        default=False,
    )

    @api.onchange('custom_currency_rate')
    def _onchange_custom_currency_rate(self):
        if not self.custom_currency_rate and self.sheet_id:
            self.currency_rate = self.sheet_id.currency_rate

    currency_rate = fields.Float(
        string="Currency Rate",
        default=1,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    list_price = fields.Float(
        string="List Price",
    )

    discount_margin = fields.Float(
        string="Discount Margin %",
    )

    net_discount_price = fields.Float(
        string="Net Dis. Price",
        compute="_compute_amounts",
        store=True,
        readonly=False,
    )

    freight_per_unit = fields.Float(
        string="Freight per Unit",
    )

    factor = fields.Float(
        string="Factor +/-",
    )

    tax_duty = fields.Float(
        string="Tax / Duty",
    )

    unit_ex_gst = fields.Float(
        string="Unit EX GST",
        compute="_compute_amounts",
        store=True,
    )
    #unit_ex_gst_corrected round of unit gst in 100
    
    unit_ex_gst_corrected = fields.Float(
        string="Unit EX GST",
        compute="_compute_amounts",
        store=True,
    )

    total_ex_gst = fields.Float(
        string="Total EX GST",
        compute="_compute_amounts",
        store=True,
    )

    gst_amount = fields.Float(
        string="GST @18%",
        compute="_compute_amounts",
        store=True,
    )

    total_inc_gst = fields.Float(
        string="Total Inc. GST",
        compute="_compute_amounts",
        store=True,
    )

    is_cnf = fields.Boolean(
        related="sheet_id.is_cnf",
        store=False,
    )
    unit_cnf_without_taxes = fields.Float(
    string="Unit C&F without taxes",
    compute="_compute_amounts",
    store=True,
    )
    # Add FIEDLS in TenderWorkingSheetLine class
    total_cnf_without_taxes = fields.Float(
        string="Total C&F Karachi without taxes",
        compute="_compute_amounts",
        store=True,
    )

    custom_duties_taxes_caa = fields.Float(
        string="Custom duties, taxes & CAA charges",
        compute="_compute_amounts",
        store=True,
    )

    local_transport_clearance = fields.Float(
        string="Local Transportation & Custom Clearance Charges",
        compute="_compute_amounts",
        store=True,
    )

    custom_duty_tax_id = fields.Many2one(
        "account.tax",
        string="Custom Duty Tax",
        help="Tax used to calculate Custom duties, taxes & CAA charges (uses this tax's %)",
    )

    local_transport_tax_id = fields.Many2one(
        "account.tax",
        string="Local Transport Tax",
        help="Tax used to calculate Local Transportation & Custom Clearance charges (uses this tax's %)",
    )

    total_cnf_at_site = fields.Float(
        string="Total C&F at site with taxes & Expenses",
        compute="_compute_amounts",
        store=True,
    )

    @api.onchange("product_id")
    def _onchange_product(self):
        if self.product_id:
            self.list_price = self.product_id.lst_price

    @api.depends(
    "qty",
    "currency_rate",
    "list_price",
    "discount_margin",
    "freight_per_unit",
    "factor",
    "tax_duty",
    "custom_duty_tax_id",
    "local_transport_tax_id",
)
    def _compute_amounts(self):
        Tax = self.env["account.tax"]

        for rec in self:

            # Net Discount Price
            rec.net_discount_price = (
                rec.list_price
                - (rec.list_price * rec.discount_margin / 100.0)
            )

            # Factor
            factor = rec.factor or 1.0

            # Tax/Duty Multiplier
            duty = 1 + ((rec.tax_duty or 0.0) / 100.0)

            # Unit EX GST
            rec.unit_ex_gst = (
                (
                    (rec.net_discount_price * factor)
                    + rec.freight_per_unit
                )
                * rec.tax_duty
                * rec.currency_rate
            )

            # Rounded Value
            rec.unit_ex_gst_corrected = round(rec.unit_ex_gst / 100.0) * 100

            # Total EX GST
            rec.total_ex_gst = (
                rec.unit_ex_gst_corrected
                * rec.qty
            )

                # Unit C&F without taxes
            rec.unit_cnf_without_taxes = (
                (rec.net_discount_price * factor) + rec.freight_per_unit
            ) * rec.currency_rate

            # Total C&F Karachi without taxes
            rec.total_cnf_without_taxes = rec.unit_cnf_without_taxes * rec.qty

            # Custom duties, taxes & CAA charges (25%)
            custom_duty_percent = (
            rec.custom_duty_tax_id.amount if rec.custom_duty_tax_id else 0.0
            )
            rec.custom_duties_taxes_caa = (
                rec.total_cnf_without_taxes * (custom_duty_percent / 100.0)
            )

            # --- Local Transportation & Custom Clearance (from tax %, not fixed 5%) ---
            local_transport_percent = (
                rec.local_transport_tax_id.amount if rec.local_transport_tax_id else 0.0
            )
            rec.local_transport_clearance = (
                rec.total_cnf_without_taxes * (local_transport_percent / 100.0)
            )
            # Total C&F at site with taxes & Expenses
            rec.total_cnf_at_site = (
                rec.total_cnf_without_taxes 
                + rec.custom_duties_taxes_caa 
                + rec.local_transport_clearance
            )



            # Search GST 18%
            gst_tax = Tax.search(
                [
                    ("tax_group_id.name", "=", "GST 18%"),
                ],
                limit=1,
            )
             # jab cnf tick hoga worksheet me  tau ye taxes banana zaroori hai
            # cnf_tax_1 = Tax.search(
            #     [("tax_group_id.name", "=", "cnf")],
            #     limit=1,
            # )
            # cnf_tax_2 = Tax.search(
            #     [("tax_group_id.name", "=", "cnf")],
            #     limit=1,
            # )

            gst_percent = gst_tax.amount if gst_tax else 0.0

            # GST Amount
            rec.gst_amount = (
                rec.total_ex_gst
                * 0.18
            )

            # Total Including GST
            rec.total_inc_gst = (
                rec.total_ex_gst
                + rec.gst_amount
            )