# -*- coding: utf-8 -*-
{
    'name': "custom_sales",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

   'depends': ['base','sale','sale_management','account','purchase','stock','bi_sale_purchase_discount_with_tax','event'],

    'data': [
        'report/inherit_sale_report.xml',
        'views/views.xml',
         'report/inherit_event_report.xml'
    ],
    'demo': [
        'demo/demo.xml',
    ],
}