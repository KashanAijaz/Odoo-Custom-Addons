{
    "name": "TDC Tender Management",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "summary": "Tender Management System",

    "author": "Techno Digi Codes",

    "depends": [
        "base",
        "product",
        "mail",
        "project",
        "base_accounting_kit",
        "sale",
        "hs_code_management"
    ],

    "data": [
        
        "security/tdc_tender_security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        'data/tender_sequence.xml',
        "views/product_view.xml",
        "views/other_info_hide.xml",
        "views/sale_field_hide.xml",
        "views/tdc_res_partner_views.xml",

        "views/upcoming_tender_views.xml",
        "views/organization_views.xml",
        "views/instrument.xml",
        "views/tender_views.xml" ,
        "views/payment_method_views.xml" ,
        # "views/tender_notification_views.xml",
        # "views/tender_notification_settings_views.xml",
        'views/tdc_tender_sale_order_wizard_views.xml',

        'reports/report_technical_quotation.xml',
        'reports/technical_quotation_template.xml',
        'reports/report_financial_quotation.xml',
        'reports/financial_quotation_template.xml',
        'reports/report_techno_financial_quotation.xml',
        'reports/techno_financial_quotation_template.xml',
        "views/earnest_money.xml" , 
        'views/tdc_performance_bond_views.xml',   
        "views/tender_source_views.xml" ,    
        'views/tdc_incoterms_views.xml', 
        "views/working_sheet_views.xml",
        "views/sale_order_views.xml",
        'views/sale_order_actions.xml',
        'wizard/tdc_create_loa_wizard_views.xml',
        # "data/ir_cron.xml",
        
        
      
        
        
      
    ],

    "installable": True,
    "application": True,
    "license": "LGPL-3",
    "assets": {
        "web.assets_backend": [
            #"tdc_tender/static/src/js/notification_systray.js",
            #"tdc_tender/static/src/xml/notification_systray.xml",
        ],
    },
  
}