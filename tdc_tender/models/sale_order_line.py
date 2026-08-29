from odoo import api, fields, models


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