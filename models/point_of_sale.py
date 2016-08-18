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


class pos_session(osv.osv):
    _name = _inherit = 'pos.session'

    def open_frontend_cb(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if not ids:
            return {}
        for session in self.browse(cr, uid, ids, context=context):
            if session.user_id.id != uid:
                raise UserError(_("You cannot use the session of another users. This session is owned by %s. "
                                    "Please first close this one to use this point of sale.") % session.user_id.name)
        context.update({'active_id': ids[0]})
        return {
            'type' : 'ir.actions.act_url',
            'target': 'self',
            'url':   '/pos/web/',
        }


class pos_order(osv.osv):
    _name = _inherit = "pos.order"


    def _amount_all(self, cr, uid, ids, name, args, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_paid': 0.0,
                'amount_return':0.0,
                'amount_tax':0.0,
                'amount_roundoff':0.0,
            }
            val1 = val2 = round_off = 0.0
            cur = order.pricelist_id.currency_id
            for payment in order.statement_ids:
                res[order.id]['amount_paid'] +=  payment.amount
                res[order.id]['amount_return'] += (payment.amount < 0 and payment.amount or 0)
            for line in order.lines:
                val1 += self._amount_line_tax(cr, uid, line, order.fiscal_position_id, context=context)
                val2 += line.price_subtotal
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val1)
            amount_untaxed = cur_obj.round(cr, uid, cur, val2)
            sub_total = res[order.id]['amount_tax'] + amount_untaxed
            remain = (sub_total*100)%100
            if remain !=0:
                if remain < 50:
                    round_off = -remain
                else:
                    round_off = 100 - remain
            res[order.id]['amount_roundoff'] = round_off/100
            res[order.id]['amount_total'] = res[order.id]['amount_tax'] + amount_untaxed + res[order.id]['amount_roundoff']
        return res


    _columns = {
                 'type': fields.selection([('order', 'Order'),
                                   ('return', 'Return')],
                                  'Order Type', readonly=True, copy=False),
                'amount_roundoff': fields.function(_amount_all, string='Roundoff', digits=0, multi='all'),
                'amount_tax': fields.function(_amount_all, string='Taxes', digits=0, multi='all'),
                'amount_total': fields.function(_amount_all, string='Total', digits=0,  multi='all'),
                'amount_paid': fields.function(_amount_all, string='Paid', states={'draft': [('readonly', False)]}, readonly=True, digits=0, multi='all'),
                'amount_return': fields.function(_amount_all, string='Returned', digits=0, multi='all'),

                }




    _defaults = {
        'type': 'order',
    }


    def refund(self, cr, uid, ids, context=None):
        """Create a copy of order  for refund order"""
        clone_list = []
        line_obj = self.pool.get('pos.order.line')
        
        for order in self.browse(cr, uid, ids, context=context):
            current_session_ids = self.pool.get('pos.session').search(cr, uid, [
                ('state', '!=', 'closed'),
                ('user_id', '=', uid)], context=context)
            if not current_session_ids:
                raise UserError(_('To return product(s), you need to open a session that will be used to register the refund.'))

            clone_id = self.copy(cr, uid, order.id, {
                'name': order.name + ' REFUND', # not used, name forced by create
                'type':'return',
                'session_id': current_session_ids[0],
                'date_order': time.strftime('%Y-%m-%d %H:%M:%S'),
            }, context=context)
            clone_list.append(clone_id)

        for clone in self.browse(cr, uid, clone_list, context=context):
            for order_line in clone.lines:
                line_obj.write(cr, uid, [order_line.id], {
                    'qty': -order_line.qty
                }, context=context)

        abs = {
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id':clone_list[0],
            'view_id': False,
            'context':context,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
        return abs
    def _create_account_move_line(self, cr, uid, ids, session=None, move_id=None, context=None):
        # Tricky, via the workflow, we only have one id in the ids variable
        """Create a account move line of order grouped by products or not."""
        account_move_obj = self.pool.get('account.move')
        account_tax_obj = self.pool.get('account.tax')
        property_obj = self.pool.get('ir.property')
        cur_obj = self.pool.get('res.currency')

        #session_ids = set(order.session_id for order in self.browse(cr, uid, ids, context=context))

        if session and not all(session.id == order.session_id.id for order in self.browse(cr, uid, ids, context=context)):
            raise UserError(_('Selected orders do not have the same session!'))

        grouped_data = {}
        have_to_group_by = session and session.config_id.group_by or False

        for order in self.browse(cr, uid, ids, context=context):
            move_lines = []
            if order.account_move:
                continue
            if order.state != 'paid':
                continue

            current_company = order.sale_journal.company_id

            group_tax = {}
            account_def = property_obj.get(cr, uid, 'property_account_receivable_id', 'res.partner', context=context)

            order_account = order.partner_id and \
                            order.partner_id.property_account_receivable_id and \
                            order.partner_id.property_account_receivable_id.id or \
                            account_def and account_def.id

            if move_id is None:
                # Create an entry for the sale
                move_id = self._create_account_move(cr, uid, order.session_id.start_at, order.name, order.sale_journal.id, order.company_id.id, context=context)

            move = account_move_obj.browse(cr, SUPERUSER_ID, move_id, context=context)

            def insert_data(data_type, values):
                # if have_to_group_by:

                sale_journal_id = order.sale_journal.id

                # 'quantity': line.qty,
                # 'product_id': line.product_id.id,
                values.update({
                    'ref': order.name,
                    'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(order.partner_id).id or False,
                    'journal_id' : sale_journal_id,
                    'date' : fields.date.context_today(self, cr, uid, context=context),
                    'move_id' : move_id,
                })

                if data_type == 'product':
                    key = ('product', values['partner_id'], (values['product_id'], values['name']), values['analytic_account_id'], values['debit'] > 0)
                elif data_type == 'tax':
                    key = ('tax', values['partner_id'], values['tax_line_id'], values['debit'] > 0)
                elif data_type == 'counter_part':
                    key = ('counter_part', values['partner_id'], values['account_id'], values['debit'] > 0)
                elif data_type == 'round_off':
                    key = ('round_off', values['partner_id'], values['account_id'], values['debit'] > 0,values['credit'] > 0)
                else:
                    return

                grouped_data.setdefault(key, [])

                # if not have_to_group_by or (not grouped_data[key]):
                #     grouped_data[key].append(values)
                # else:
                #     pass

                if have_to_group_by:
                    if not grouped_data[key]:
                        grouped_data[key].append(values)
                    else:
                        for line in grouped_data[key]:
                            if line.get('tax_code_id') == values.get('tax_code_id'):
                                current_value = line
                                current_value['quantity'] = current_value.get('quantity', 0.0) +  values.get('quantity', 0.0)
                                current_value['credit'] = current_value.get('credit', 0.0) + values.get('credit', 0.0)
                                current_value['debit'] = current_value.get('debit', 0.0) + values.get('debit', 0.0)
                                break
                        else:
                            grouped_data[key].append(values)
                else:
                    grouped_data[key].append(values)

            #because of the weird way the pos order is written, we need to make sure there is at least one line, 
            #because just after the 'for' loop there are references to 'line' and 'income_account' variables (that 
            #are set inside the for loop)
            #TOFIX: a deep refactoring of this method (and class!) is needed in order to get rid of this stupid hack
            assert order.lines, _('The POS order must have lines when calling this method')
            # Create an move for each order line

            cur = order.pricelist_id.currency_id
            for line in order.lines:
                amount = line.price_subtotal

                # Search for the income account
                if  line.product_id.property_account_income_id.id:
                    income_account = line.product_id.property_account_income_id.id
                elif line.product_id.categ_id.property_account_income_categ_id.id:
                    income_account = line.product_id.categ_id.property_account_income_categ_id.id
                else:
                    raise UserError(_('Please define income '\
                        'account for this product: "%s" (id:%d).') \
                        % (line.product_id.name, line.product_id.id))

                name = line.product_id.name
                if line.notice:
                    # add discount reason in move
                    name = name + ' (' + line.notice + ')'

                # Create a move for the line for the order line
                insert_data('product', {
                    'name': name,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'account_id': income_account,
                    'analytic_account_id': self._prepare_analytic_account(cr, uid, line, context=context),
                    'credit': ((amount>0) and amount) or 0.0,
                    'debit': ((amount<0) and -amount) or 0.0,
                    'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(order.partner_id).id or False
                })

                # Create the tax lines
                taxes = []
                for t in line.tax_ids_after_fiscal_position:
                    if t.company_id.id == current_company.id:
                        taxes.append(t.id)
                if not taxes:
                    continue
                for tax in account_tax_obj.browse(cr,uid, taxes, context=context).compute_all(line.price_unit * (100.0-line.discount) / 100.0, cur, line.qty)['taxes']:
                    insert_data('tax', {
                        'name': _('Tax') + ' ' + tax['name'],
                        'product_id': line.product_id.id,
                        'quantity': line.qty,
                        'account_id': tax['account_id'] or income_account,
                        'credit': ((tax['amount']>0) and tax['amount']) or 0.0,
                        'debit': ((tax['amount']<0) and -tax['amount']) or 0.0,
                        'tax_line_id': tax['id'],
                        'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(order.partner_id).id or False
                    })

            # counterpart
            insert_data('counter_part', {
                'name': _("Trade Receivables"), #order.name,
                'account_id': order_account,
                'credit': ((order.amount_total < 0) and -order.amount_total) or 0.0,
                'debit': ((order.amount_total > 0) and order.amount_total) or 0.0,
                'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(order.partner_id).id or False
            })
            
            #~ # roundoff
            #~ insert_data('round_off', {
                #~ 'name': _("Round Off"), #order.name,
                #~ 'account_id': order_account,
                #~ 'credit': ((order.amount_roundoff  > 0) and order.amount_total) or 0.0,
                #~ 'debit': ((order.amount_total < 0) and -order.amount_total) or 0.0,
            #~ })

            order.write({'state':'done', 'account_move': move_id})
            
        credit=debit=0.0
        all_lines = []
        for group_key, group_data in grouped_data.iteritems():
            for value in group_data:
                all_lines.append((0, 0, value),)
                debit+=value['debit']
                credit+=value['credit']
        #~ if credit > debit :
        if credit > 0.0 or debit > 0.0:
            move_line = {
                'ref': order.name,
                'journal_id' : order.sale_journal.id,
                'date' : fields.date.context_today(self, cr, uid, context=context),
                'move_id' : move_id,
                'name': _("Round Off"), #order.name,
                'account_id': order_account,
                'credit': ((credit < debit)and (debit-credit))or 0.0,
                'debit': ((credit > debit)and (credit-debit))or 0.0
                    }
            all_lines.append((0,0,move_line))
        if move_id: #In case no order was changed
            account_move_obj.write(cr, SUPERUSER_ID, [move_id], {'line_ids':all_lines}, context=context)
            move = account_move_obj.browse(cr,uid,move_id)
            account_move_obj.post(cr, SUPERUSER_ID, [move_id], context=context)

        return True
