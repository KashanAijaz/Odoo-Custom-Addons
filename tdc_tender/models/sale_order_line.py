from odoo import api, fields, models
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    currency_rate = fields.Float(
        string="Currency Rate",
        readonly=True,
    )

    list_price = fields.Float(
        string="List Price",
        readonly=True,
    )

    is_cnf = fields.Boolean(
        string="C&F",
        readonly=True,
    )

    total_cnf_at_site = fields.Float(
        string="Total C&F at Site",
        readonly=True,
    )

    unit_cnf_at_site = fields.Float(
            string="Total C&F at Site",
            readonly=True,
        )

    discount_margin = fields.Float(
        string="Discount %",
        readonly=True,
    )

    net_discount_price = fields.Float(
        string="Net Discount Price",
        readonly=True,
    )
    
    technical_key_features = fields.Html(
        string='Key Features',
        compute='_compute_technical_fields',
        store=True,
        readonly=False,
        precompute=True
    )
    tender_specification = fields.Html(
        string='Technical Specification',
        compute='_compute_technical_fields',
        store=True,
        readonly=False,
        precompute=True
    )
    technical_power_supply = fields.Html(
        string='Power Supply',
        compute='_compute_technical_fields',
        store=True,
        readonly=False,
        precompute=True
    )
    country_of_origin = fields.Many2one(
        'res.country',
        string='Country of Origin',
        related='product_id.country_of_origin',
        store=True,
        readonly=True
    )
    
    @api.depends('product_id')
    def _compute_technical_fields(self):
        for line in self:
            if line.product_id:
                line.technical_key_features = line.product_id.technical_key_features
                line.tender_specification = line.product_id.tender_specification
                line.technical_power_supply = line.product_id.technical_power_supply

    # @api.depends('product_uom_qty', 'price_unit', 'tax_ids', 'is_cnf', 'total_cnf_at_site')
    # def _compute_amount(self):
    #     for line in self:
    #         super(SaleOrderLine, line)._compute_amount()
    #         if line.is_cnf:
    #             line.price_subtotal = line.total_cnf_at_site
    #             line.price_total = line.total_cnf_at_site
    #             line.price_tax = 0.0

    # @api.depends('total_cnf_at_site', 'is_cnf')
    # def _compute_price_unit_cnf(self):
    #     for line in self:
    #         if line.is_cnf:
    #             line.price_unit = line.total_cnf_at_site
        
    is_line_locked = fields.Boolean(
        string="Line Locked",
        compute="_compute_is_line_locked",
        store=False,
    )

    @api.depends(
        "order_id.is_tender_sale",
        "order_id.tender_workflow_state",
    )
    def _compute_is_line_locked(self):
        is_manager = self.env.user.has_group("tdc_tender.group_tender_manager")
        is_admin_control = self.env.user.has_group("tdc_tender.group_tender_payment_admin")
        has_bypass = is_manager or is_admin_control

        for line in self:
            if has_bypass:
                # Admin Control / Manager -> lines always editable.
                line.is_line_locked = False
            else:
                order = line.order_id
                # Non-admin -> locked for the whole tender lifecycle EXCEPT
                # at the Letter of Acceptance stage, where re-pricing/qty
                # edits are allowed.
                line.is_line_locked = (
                    bool(order.is_tender_sale)
                    and order.tender_workflow_state != "letter_of_acceptance"
                )

    @api.depends("product_id")
    def _compute_technical_fields(self):
        for line in self:
            if line.product_id:
                line.technical_key_features = line.product_id.technical_key_features
                line.tender_specification = line.product_id.tender_specification
                line.technical_power_supply = line.product_id.technical_power_supply

    def unlink(self):
        # NEW: block deleting order lines from the UI when the line is
        # "locked" per our tender workflow rules — mirrors the same
        # condition used in is_line_locked (group_tender_payment_admin /
        # group_tender_manager bypass, everyone else blocked except during
        # 'letter_of_acceptance').
        is_manager = self.env.user.has_group("tdc_tender.group_tender_manager")
        is_admin_control = self.env.user.has_group("tdc_tender.group_tender_payment_admin")
        has_bypass = is_manager or is_admin_control

        if not has_bypass:
            for line in self:
                order = line.order_id
                if order.is_tender_sale and order.tender_workflow_state != "letter_of_acceptance":
                    raise UserError(
                        "You cannot delete at this stage."
                    )

        return super().unlink()