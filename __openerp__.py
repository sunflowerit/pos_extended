# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'POS Extended Reports',
    'version' : '1.1',
    'summary': 'POS Extended Reports',
    'sequence': 30,
    'description': """ POS extended for reports and kot
    """,
    'author': "Senthilnatha G",
    'website': "https://www.senthilnathan,info",

    'price': 49,
    'currency': 'EUR',
    'category' : 'Point Of Sale',
    'images' : [],
    'depends' : ['base','sale','point_of_sale','stock','pos_restaurant','pos_discount','account'],
    'data': [

         'sales_report.xml',
         
         'wizard/pos_details_total.xml',
         'wizard/pos_discount.xml',
        
         'views/pos_view.xml',
         'views/kot_view.xml',
         'views/pos_report.xml',
         'views/templates.xml',
         'views/views.xml',

         
         'views/report_kitchen_receipt.xml',
         'views/report_detailsofsales.xml',
         'views/report_detailsofdiscount.xml',
         'views/report_detailsofsalestotal.xml',
         'views/pos_report.xml',
         
         
         
         
         'report/pos_order_report_view.xml',
         'report/dump_order_report_view.xml',

         
    ],
    'demo': [
        
    ],
    'qweb': [ 
    'static/src/xml/kitchen.xml',
    'static/src/xml/discount_amount.xml',
    'static/src/xml/pos.xml',
        
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OEEL-1',
}
