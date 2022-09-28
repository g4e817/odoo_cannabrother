# -*- coding: utf-8 -*-
{
    'name': "Automatischer Workflow Erweiterung",

    'summary': """Anpassung des automatischen Workflows""",
    'license': 'OPL-1',
    'description': """
        Long description of module's purpose
    """,

    'author': "Mountain Media",
    'website': "https://mountain.co.at",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['common_connector_library', 'custom_invoice_template', 'account_payment_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
