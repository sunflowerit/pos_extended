# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import pytz
import time
from openerp import tools
from openerp.osv import osv
from openerp.report import report_sxw


class pos_details_discount(report_sxw.rml_parse):

  

    def _get_invoice(self, inv_id):
        res={}
        if inv_id:
            self.cr.execute("select number from account_invoice as ac where id = %s", (inv_id,))
            res = self.cr.fetchone()
            return res[0] or 'Draft'
        else:
            return  ''

    def _get_all_users(self):
        user_obj = self.pool.get('res.users')
        return user_obj.search(self.cr, self.uid, [])

    def _discount_details(self, form):
        pos_obj = self.pool.get('pos.order')
        user_obj = self.pool.get('res.users')
        data = []
        result = {}
        self.total_discount=0.0
        self.discount_percent_five_total=0.0
        self.discount_percent_ten_total=0.0
        self.discount_percent_twenty_total=0.0
        self.discount_percent_thirty_total=0.0
        self.discount_percent_forty_total=0.0
        self.discount_percent_fifty_total=0.0
        self.discount_percent_ninetynine_total=0.0
        self.discount_percent_hundred_total=0.0
        
        self.total_discount_qty=0.0
        self.discount_percent_five_qty=0.0
        self.discount_percent_ten_qty=0.0
        self.discount_percent_twenty_qty=0.0
        self.discount_percent_thirty_qty=0.0
        self.discount_percent_forty_qty=0.0
        self.discount_percent_fifty_qty=0.0
        self.discount_percent_ninetynine_qty=0.0
        self.discount_percent_hundred_qty=0.0
    
        user_ids = form['user_ids'] or self._get_all_users()
        company_id = user_obj.browse(self.cr, self.uid, self.uid).company_id.id
        user = self.pool['res.users'].browse(self.cr, self.uid, self.uid)
        tz_name = user.tz or self.localcontext.get('tz') or 'UTC'
        user_tz = pytz.timezone(tz_name)
        between_dates = {}
        for date_field, delta in {'date_start': {'days': 0}, 'date_end': {'days': 1}}.items():
            timestamp = datetime.datetime.strptime(form[date_field] + ' 00:00:00', tools.DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(**delta)
            timestamp = user_tz.localize(timestamp).astimezone(pytz.utc)
            between_dates[date_field] = timestamp.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)

        pos_ids = pos_obj.search(self.cr, self.uid, [
            ('date_order', '>=',  between_dates['date_start']),
            ('date_order', '<',  between_dates['date_end']),
            ('user_id', 'in', user_ids),
            ('state', 'in', ['done', 'paid', 'invoiced']),
            ('company_id', '=', company_id)
        ])
        for pos in pos_obj.browse(self.cr, self.uid, pos_ids, context=self.localcontext):
            discount =0.0
            discount_percent=0.0
            for pol in pos.lines:
                discount += ((pol.price_unit * pol.qty) * (pol.discount / 100))
                self.total_discount += ((pol.price_unit * pol.qty) * (pol.discount / 100))
            if discount != 0.0:
                discount_percent =  (discount *100) /(pos.amount_total + discount)
            if discount_percent >0.0:
                self.total_discount_qty +=  1
                if discount_percent <= 5.0:
                    self.discount_percent_five_total +=  discount
                    self.discount_percent_five_qty +=  1
                if discount_percent > 5.0 and discount_percent <= 10.0:
                    self.discount_percent_ten_total +=  discount
                    self.discount_percent_ten_qty +=  1
                if discount_percent > 10.0 and discount_percent <= 20.0:
                    self.discount_percent_twenty_total +=  discount
                    self.discount_percent_twenty_qty +=  1
                if discount_percent > 20.0 and discount_percent <=30.0:
                    self.discount_percent_thirty_total +=  discount
                    self.discount_percent_thirty_qty +=  1
                if discount_percent > 30.0 and discount_percent <=40.0:
                    self.discount_percent_forty_total +=  discount
                    self.discount_percent_forty_qty +=  1
                if discount_percent > 40.0 and discount_percent <=50.0:
                    self.discount_percent_fifty_total +=  discount
                    self.discount_percent_fifty_qty +=  1
                if discount_percent > 50.0 and discount_percent <=99.0:
                    self.discount_percent_ninetynine_total +=  discount
                    self.discount_percent_ninetynine_qty +=  1
                if discount_percent == 100.0:
                    self.discount_percent_hundred_total +=  discount
                    self.discount_percent_hundred_qty +=  1
                result = {
                    'name': pos.name,
                    'total': pos.amount_total,
                    'discount': discount, 
                    'date_order': pos.date_order, 
                    'percent': discount_percent, 
                }
                data.append(result)
        if data:
            return data
        else:
            return {}


    def _get_sum_discount(self):
        #code for the sum of discount value
        return self.total_discount or 0.0
        
    def _get_sum_discount_five_percent(self):
        #code for the sum of discount value
        return self.discount_percent_five_total or 0.0
        
    def _get_sum_discount_ten_percent(self):
        #code for the sum of discount value
        return self.discount_percent_ten_total or 0.0
        
    def _get_sum_discount_twenty_percent(self):
        #code for the sum of discount value
        return self.discount_percent_twenty_total or 0.0

   
    def _get_sum_discount_thirty_percent(self):
        #code for the sum of discount value
        return self.discount_percent_thirty_total or 0.0

    def _get_sum_discount_forty_percent(self):
        #code for the sum of discount value
        return self.discount_percent_forty_total or 0.0
        
    def _get_sum_discount_fifty_percent(self):
        #code for the sum of discount value
        return self.discount_percent_fifty_total or 0.0
        
    def _get_sum_discount_ninetynine_percent(self):
        #code for the sum of discount value
        return self.discount_percent_ninetynine_total or 0.0
        
    def _get_sum_discount_hundred_percent(self):
        #code for the sum of discount value
        return self.discount_percent_hundred_total or 0.0

    def _get_sum_discount_qty(self):
        #code for the sum of discount value
        return self.total_discount_qty or 0.0
        
    def _get_sum_discount_five_percent_qty(self):
        #code for the sum of discount value
        return self.discount_percent_five_qty or 0.0
        
    def _get_sum_discount_ten_percent_qty(self):
        #code for the sum of discount value
        return self.discount_percent_ten_qty or 0.0
        
    def _get_sum_discount_twenty_percent_qty(self):
        #code for the sum of discount value
        return self.discount_percent_twenty_qty or 0.0

   
    def _get_sum_discount_thirty_percent_qty(self):
        #code for the sum of discount value
        return self.discount_percent_thirty_qty or 0.0

    def _get_sum_discount_forty_percent_qty(self):
        #code for the sum of discount value
        return self.discount_percent_forty_qty or 0.0
        
    def _get_sum_discount_fifty_percent_qty(self):
        #code for the sum of discount value
        return self.discount_percent_fifty_qty or 0.0
        
    def _get_sum_discount_ninetynine_percent_qty(self):
        #code for the sum of discount value
        return self.discount_percent_ninetynine_qty or 0.0
        
    def _get_sum_discount_hundred_percent_qty(self):
        #code for the sum of discount value
        return self.discount_percent_hundred_qty or 0.0

   
    def _get_user_names(self, user_ids):
        user_obj = self.pool.get('res.users')
        return ', '.join(map(lambda x: x.name, user_obj.browse(self.cr, self.uid, user_ids)))

    def __init__(self, cr, uid, name, context):
        super(pos_details_discount, self).__init__(cr, uid, name, context=context)
        self.total = 0.0
        self.qty = 0.0
        self.total_invoiced = 0.0
        self.discount = 0.0
        self.total_discount = 0.0
        self.localcontext.update({
            'time': time,
            'getsumdisc': self._get_sum_discount,
            'getsumdiscfivepercent': self._get_sum_discount_five_percent,
            'getsumdisctenpercent': self._get_sum_discount_ten_percent,
            'getsumdisctwentypercent': self._get_sum_discount_twenty_percent,
            'getsumdiscthirtypercent': self._get_sum_discount_thirty_percent,
            'getsumdiscfortypercent': self._get_sum_discount_forty_percent,
            'getsumdiscfiftypercent': self._get_sum_discount_fifty_percent,
            'getsumdiscninetyninepercent': self._get_sum_discount_ninetynine_percent,
            'getsumdischundredpercent': self._get_sum_discount_hundred_percent,
            'getsumdiscqty': self._get_sum_discount_qty,
            'getsumdiscfivepercentqty': self._get_sum_discount_five_percent_qty,
            'getsumdisctenpercentqty': self._get_sum_discount_ten_percent_qty,
            'getsumdisctwentypercentqty': self._get_sum_discount_twenty_percent_qty,
            'getsumdiscthirtypercentqty': self._get_sum_discount_thirty_percent_qty,
            'getsumdiscfortypercentqty': self._get_sum_discount_forty_percent_qty,
            'getsumdiscfiftypercentqty': self._get_sum_discount_fifty_percent_qty,
            'getsumdiscninetyninepercentqty': self._get_sum_discount_ninetynine_percent_qty,
            'getsumdischundredpercentqty': self._get_sum_discount_hundred_percent_qty,
            'discount_details':self._discount_details,
            'get_user_names': self._get_user_names,
        })


 



class report_pos_details_discount(osv.AbstractModel):
    _name = 'report.point_of_sale.report_detailsofdiscount'
    _inherit = 'report.abstract_report'
    _template = 'point_of_sale.report_detailsofdiscount'
    _wrapped_report_class = pos_details_discount
