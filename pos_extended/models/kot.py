# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import time
from datetime import datetime
import uuid
import sets

from functools import partial

import openerp
import openerp.addons.decimal_precision as dp
from openerp import tools, models, SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools import float_is_zero
from openerp.tools.translate import _
from openerp.exceptions import UserError


_logger = logging.getLogger(__name__)

class pos_order(osv.osv):
    _name = _inherit = "pos.order"
    
    _columns = {
    'kot_order_ids':fields.one2many('kitchen.order','pos_order_id','Kitchen Order'),
    }
    def create_kot_from_ui(self, cr, uid, orders, context=None):
        print orders
        submitted_references = str(orders['name'])
        kot_obj = self.pool.get('kitchen.order')
        existing_order_ids = self.search(cr, uid, [('pos_reference', '=', submitted_references)], context=context)
        if existing_order_ids:
            orders.update({'pos_order_id':order_id})
            #~ pass
        else:
            pass
            #~ order_id = self.create(cr, uid, orders)
            #~ orders.update({'pos_order_id':order_id})
        order_id = kot_obj.create(cr, uid, orders)
        #~ order = kot_obj.browse(cr,uid,order_id)
        return order_id
class pos_order_line(osv.osv):
    _name = _inherit = "pos.order.line"
    
    _columns = {
      'kot_line_id':fields.many2one('kitchen.order.line','Kitchen Order Line'),
    }

class kitchen_order(osv.osv):
    _name = "kitchen.order"
    _inherit = ['pos.order']


    _columns = {
                'name':fields.char('Name',size=128),
                'type': fields.selection([('order', 'Order'),
                                   ('return', 'Return')],
                                  'Order Type', readonly=True, copy=False),
                 'lines':fields.one2many('kitchen.order.line','order_id','Lines'),
                 'pos_order_id': fields.many2one('pos.order', 'POS Order'),
                 'company_id':fields.many2one('res.company', 'Company', required=True, readonly=True),
                }

    _defaults ={
    'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }

    def create(self, cr, uid, values, context=None):
       
        return super(kitchen_order, self).create(cr, uid, values, context=context)

    _defaults = {
        'type': 'order',
    }
class kitchen_order_line(osv.osv):
    _name = 'kitchen.order.line'
    _inherit= ['pos.order.line']

    _columns = {
                 'order_id':fields.many2one('kitchen.order','Order'),
                 'notes':fields.text('Notes'),
                 
                }


