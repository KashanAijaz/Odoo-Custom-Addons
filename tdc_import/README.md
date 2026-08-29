# TDC Import - GD Tariff Management (Odoo 19)

Adds an **Import** top menu with a **Tariff** sub-menu to record Goods
Declaration (GD) based import tariff calculations, using HS Codes from the
`hs_code_management` module.

## Dependencies
- `hs_code_management` (must be installed first — provides `hs.code` and the
  `hs_code_id` field on `product.template`)
- `product`, `account`, `uom`

## Menu structure
```
Import
├── Tariff              -> list/form of GD tariffs
├── Export to Excel     -> wizard to export a date/vendor filtered report
└── Configuration
```

## Header fields (tdc.import.tariff)
- GD No. (`dg_no`), GD Date, Vendor
- Currency of Import (EUR, USD, ...), GD Payment Exchange Rate
- Insurance % (on CFR value) — default 1.0
- Landing Charges % (on CFR value) — default 1.0

## Line fields (tdc.import.tariff.line)
Selecting **Item** (product) automatically fetches:
- HS Code (`product.hs_code_id`)
- CD %, RD %, ACD % (from the HS Code record)

You only need to enter **Qty**, **UOM** and **Assessed Unit Value** (in the
Currency of Import). Everything else is computed:

| Field | Formula |
|---|---|
| Assessed Total Value | Assessed Unit Value × Qty |
| Assessed Unit Value (PKR) | Assessed Unit Value × Exchange Rate × (1 + Insurance %) × (1 + Landing %) |
| Assessed Total Value (PKR) | Assessed Unit Value (PKR) × Qty |
| CD / RD / ACD (PKR) | Assessed Total Value (PKR) × CD/RD/ACD % |
| ST / AST / IT (PKR) | Assessed Total Value (PKR) × ST/AST/IT % |
| Total Sum Payable (PKR) | Assessed Total Value (PKR) + CD + RD + ACD + ST + AST + IT |

**Note on the calculation base:** all duty/tax percentages (CD, RD, ACD, ST,
AST, IT) are applied directly on the **Assessed Total Value (PKR)** (i.e. no
cascading base such as "value + CD" for RD, etc.), matching the columns as
listed. If your real-world GD requires a cascading base (common in some
Pakistan Customs computations, e.g. RD on Value+CD, Sales Tax on
Value+CD+RD+ACD), adjust `_compute_duties()` in `models/tariff.py`
accordingly — the structure makes this a one-line change per field.

ST, AST and IT percentages are fetched (via onchange) from the `amount`
field of the selected `account.tax` record (`st_tax_id`, `ast_tax_id`,
`it_tax_id`), then stored as editable percentage fields so they can be
overridden per line if needed.

## Design notes (Odoo 19)
- No `state` field / workflow — this is a straightforward data-entry +
  calculation model, not an approval workflow.
- No `attrs`/`states` XML attribute (deprecated) — all conditional
  behaviour uses the Odoo 17+ direct-expression syntax
  (`readonly="..."`, `invisible="..."`, `column_invisible="..."`).
- List views use the `<list>` tag (Odoo 19), not the legacy `<tree>` tag.

## Reports
- **Export to Excel** (`Import > Export to Excel`): filter by GD date range
  and/or vendor, generates and downloads an `.xlsx` file with one row per
  tariff line.
- **Print > GD Tariff Report** (PDF, available from the Tariff form's
  Print menu): one-page summary per GD with line details and totals.

## Updating the `hs_code_management` module
The `product.template` inherited field already provided is correct; it
just needs a help text and should be added to the product form view, e.g.:

```python
# hs_code_management/models/product_template.py
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hs_code_id = fields.Many2one(
        'hs.code',
        string='HS Code',
        help='Harmonized System Code used for import/export duty calculation.',
    )
```

```xml
<!-- hs_code_management/views/product_template_views.xml -->
<record id="view_product_template_form_hs_code" model="ir.ui.view">
    <field name="name">product.template.form.hs.code</field>
    <field name="model">product.template</field>
    <field name="inherit_id" ref="product.product_template_form_view"/>
    <field name="arch" type="xml">
        <field name="default_code" position="after">
            <field name="hs_code_id"/>
        </field>
    </field>
</record>
```
