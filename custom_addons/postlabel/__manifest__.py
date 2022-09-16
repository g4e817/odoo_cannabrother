# -*- coding: utf-8 -*-
{
    'name': "Postlabel",

    'summary': """Generierung von Labels für Post.at""",

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
    'depends': ['stock', 'sale', 'queue_job', 'delivery'],

    # always loaded
    'data': [
        'wizard/perform_end_of_day_widget.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/email_template.xml',
        #'views/cron.xml',
        'wizard/assignee_user_wizard.xml',
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
