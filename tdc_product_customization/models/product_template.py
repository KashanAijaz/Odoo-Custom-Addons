# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """Inherit product.template (no core file is touched) to add
    sourcing, pricing and packing/weight information required by TDC.
    """
    _inherit = 'product.template'

    # ------------------------------------------------------------------
    # System parameter key used to make the volumetric weight divisor
    # configurable without touching the code. Default value is 6000,
    # matching the industry-standard air-freight volumetric divisor.
    # Change it any time via Settings > Technical > Parameters > System
    # Parameters, using this exact key.
    # ------------------------------------------------------------------
    VOLUMETRIC_DIVISOR_PARAM = 'tdc_product_customization.volumetric_divisor'
    DEFAULT_VOLUMETRIC_DIVISOR = 6000.0

    # ------------------------------------------------------------------
    # Source Information
    # ------------------------------------------------------------------
    purchase_source = fields.Selection(
        selection=[
            ('local_purchase', 'Local Purchase'),
            ('import_purchase', 'Import Purchase'),
        ],
        string="Purchase Source",
        default='local_purchase',
        help="Indicates whether this product is sourced locally or imported. "
             "Defaults to 'Local Purchase' as requested.",
    )

    # ------------------------------------------------------------------
    # Pricing
    # ------------------------------------------------------------------
    # EXW Origin List Price carries its own currency because the origin
    # price list may be quoted in a currency different from the company's
    # currency (e.g. a supplier's EXW price list in USD while the company
    # operates in another currency).
    exw_origin_list_price_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="EXW Origin List Price Currency",
        default=lambda self: self.env.company.currency_id,
        help="Currency in which the EXW Origin List Price is expressed.",
    )
    exw_origin_list_price = fields.Monetary(
        string="EXW Origin List Price",
        currency_field='exw_origin_list_price_currency_id',
        help="Ex-Works list price at the origin/supplier, before freight, "
             "insurance and duties.",
    )

    exw_origin_net_transfer_price_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="EXW Origin Net Transfer Price Currency",
        default=lambda self: self.env.company.currency_id,
        help="Currency in which the EXW Origin Net Transfer Price is "
             "expressed.",
    )
    exw_origin_net_transfer_price = fields.Monetary(
        string="EXW Origin Net Transfer Price",
        currency_field='exw_origin_net_transfer_price_currency_id',
        help="Ex-Works net transfer price at origin, i.e. the internal "
             "transfer cost between related entities.",
    )

    # Normal Selling Rate and Competitive Selling Rate are always expressed
    # in the product's own selling currency, so we deliberately reuse the
    # standard 'currency_id' field already provided by product.template
    # (the same field used by list_price/standard_price) instead of adding
    # two more Many2one currency fields. This avoids duplicating existing
    # functionality.
    normal_selling_rate = fields.Monetary(
        string="Normal Selling Rate",
        currency_field='currency_id',
        help="Standard/normal rate at which the product is sold.",
    )
    competitive_selling_rate = fields.Monetary(
        string="Competitive Selling Rate",
        currency_field='currency_id',
        help="Discounted/competitive rate offered under competitive market "
             "conditions.",
    )

    # ------------------------------------------------------------------
    # Packing Details
    # ------------------------------------------------------------------
    net_weight = fields.Float(
        string="Net Weight",
        digits='Stock Weight',
        help="Weight of the product itself, excluding packaging.",
    )
    gross_weight = fields.Float(
        string="Gross Weight",
        digits='Stock Weight',
        help="Weight of the product including packaging material.",
    )

    # Standard Odoo (Community & Enterprise) does NOT provide Length /
    # Width / Height fields on product.template. Dimensions of this kind
    # only exist, out of the box, on stock.package.type (package/box
    # dimensions) and on shipping connectors, not on the product itself.
    # Since no reusable standard field exists at the product.template
    # level, we create them here as requested.
    product_length = fields.Float(
        string="Length (cm)",
        help="Product length, used to compute the Volumetric Weight.",
    )
    product_width = fields.Float(
        string="Width (cm)",
        help="Product width, used to compute the Volumetric Weight.",
    )
    product_height = fields.Float(
        string="Height (cm)",
        help="Product height, used to compute the Volumetric Weight.",
    )
    divisor = fields.Float(
        string="Volumetric Divisor",
        default=6000.0,
        help="Divisor used to calculate volumetric weight "
            "(commonly 5000 for courier, 6000 for air freight).",
    )
    volumetric_weight = fields.Float(
        string="Volumetric Weight (kg)",
        digits='Stock Weight',
        compute='_compute_volumetric_weight',
        store=True,
    
        help="Computed as (Length x Width x Height) / divisor. The divisor "
             "defaults to 6000 and can be changed via the system parameter "
             "'%s' without any code change." % VOLUMETRIC_DIVISOR_PARAM,
    )
    cw_weight = fields.Float(
        string="Chargeable Weight (kg)",
        digits='Stock Weight',
        compute='_compute_cw_weight',
        store=True,
        help="The highest value among Net Weight, Gross Weight and "
             "Volumetric Weight. This is the weight typically used by "
             "carriers to charge freight.",
    )

    @api.depends('product_length', 'product_width', 'product_height', 'divisor')
    def _compute_volumetric_weight(self):
        """Volumetric Weight = (Length x Width x Height) / divisor."""
        for product in self:
            divisor = product.divisor or 6000.0
            product.volumetric_weight = (
                product.product_length * product.product_width * product.product_height
            ) / divisor

    @api.depends('net_weight', 'gross_weight', 'volumetric_weight')
    def _compute_cw_weight(self):
        """Chargeable Weight = max(Net Weight, Gross Weight, Volumetric Weight)."""
        for product in self:
            product.cw_weight = max(
                product.net_weight,
                product.gross_weight,
                product.volumetric_weight,
            )

    ################################################################
    ################Child Product##################################

        # Self-referencing Many2many: ek parent product k multiple child products
    # ho sakte hain, aur aik product multiple parents ka child bhi ban sakta hai.
    
    child_product_ids = fields.Many2many(
        comodel_name='product.template',
        relation='product_template_child_rel',
        column1='parent_id',
        column2='child_id',
        string='Child Products',
        domain="[('id', '!=', id)]",
        help='Ye products is (parent) product k child hain. Sale/Purchase order '
             'mein parent product add hone par in child products ka wizard khulta hai.',
    )

    # Reverse field - optional, useful agar dekhna ho k ye product kis parent ka child hai
    parent_product_ids = fields.Many2many(
        comodel_name='product.template',
        relation='product_template_child_rel',
        column1='child_id',
        column2='parent_id',
        string='Parent Products',
    )

