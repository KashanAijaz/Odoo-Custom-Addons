# -*- coding: utf-8 -*-
{
    "name": "TDC Delivery Customization",
    "version": "19.0.1.0.0",
    "summary": "Custom delivery / installation workflow with relabeled status "
                "steps and Delivery Receipt, Installation Under Process, "
                "Installation Completed tabs on the Delivery Order (stock.picking).",
    "description": """
TDC Delivery Customization
===========================
Adds a custom, relabeled delivery/installation progress bar to the
Delivery Order (stock.picking) form, plus the following notebook pages:

* Delivery Receipt (fields shown depend on the selected Delivery Type:
  By Hand / By Courier / Bilti Transport / Customer Self Pickup)
* Installation Under Process
* Installation Completed
* Attachments (a line table similar to the Tender Evaluation attachment
  lines, always visible regardless of stage)

The real `state` field's selection is relabeled and extended in place
(assigned -> Delivery Out, done -> Satisfactory Completed, plus 3 new
in-between values), with the compute logic overridden so it doesn't get
reset by Odoo's automatic recomputation.

Also adds a "Satisfactory Completion Certificate" report under the
Print menu of the Delivery Order (currently a blank placeholder PDF).
""",
    "author": "TDC",
    "category": "Inventory/Inventory",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_picking_views.xml",
        # "reports/satisfactory_completion_certificate.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
