
from openerp import fields, models


class PosDiscountReport(models.TransientModel):
    _inherit = "pos.details"
    _name = 'pos.discount.report'
    _description = 'Discount Report'

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['date_start', 'date_end', 'user_ids'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        if res.get('id',False):
            datas['ids']=[res['id']]
        return self.pool['report'].get_action(cr, uid, [], 'point_of_sale.report_detailsofdiscount', data=datas, context=context)
