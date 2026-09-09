{
    "name": "Estate",
    "version": "1.0",
    "depends": [
        "base",
        "account",
    ],
    "application": True,
    "installable": True,
'data': [
    'security/estate_groups.xml',
    'security/ir.model.access.csv',
    'views/estate_property_views.xml',
      'views/estate_property_offer_views.xml',
    'views/estate_property_type_views.xml',
      'views/estate_property_tag_views.xml',
      'report/property_report.xml',   
      'views/estate_menus.xml',   
    'views/res_users_views.xml',  
            
],
}