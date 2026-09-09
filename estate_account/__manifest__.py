{
    "name": "Real Estate Account",
    "version": "1.0",
    "category": "Real Estate",
    "summary": "Link module between Real Estate and Accounting",
    "description": """
        Bridges the Real Estate module with the Accounting module.
    """,
    "depends": ["estate", "account"],
    "data": [
         "views/estate_property_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}