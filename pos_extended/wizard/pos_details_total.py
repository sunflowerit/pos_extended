# -*- coding: utf-8 -*-
#~ from openerp import fields, models,api

import time
from openerp.osv import osv, fields




class PosTotalDetails(osv.osv_memory):
    _inherit = "pos.details"
    _name = 'pos.details.total'
    _description = 'Total Sales Report'
    
    def print_report(self, cr, uid, ids, context=None):
        """
         To get the date and print the report
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return : retrun report
        """
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['date_start', 'date_end', 'user_ids'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        if res.get('id',False):
            datas['ids']=[res['id']]
        return self.pool['report'].get_action(cr, uid, [], 'point_of_sale.report_detailsofsalestotal', data=datas, context=context)
