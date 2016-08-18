# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

""" Fields:
      - simple
      - relations (one2many, many2one, many2many)
      - function

    Fields Attributes:
        * _classic_read: is a classic sql fields
        * _type   : field type
        * _auto_join: for one2many and many2one fields, tells whether select
            queries will join the relational table instead of replacing the
            field condition by an equivalent-one based on a search.
        * readonly
        * required
        * size
"""

import base64
import datetime as DT
import functools
import logging
import pytz
import re
import xmlrpclib
from operator import itemgetter
from psycopg2 import Binary

import openerp
import openerp.tools as tools
from openerp.sql_db import LazyCursor
from openerp.tools.translate import _
from openerp.tools import float_repr, float_round, frozendict, html_sanitize
import json
from openerp import SUPERUSER_ID

# deprecated; kept for backward compatibility only
_get_cursor = LazyCursor

EMPTY_DICT = frozendict()

_logger = logging.getLogger(__name__)

def _symbol_set(symb):
    if symb is None or symb == False:
        return None
    elif isinstance(symb, unicode):
        return symb.encode('utf-8')
    return str(symb)


class _column(object):
    """ Base of all fields, a database column

        An instance of this object is a *description* of a database column. It will
        not hold any data, but only provide the methods to manipulate data of an
        ORM record or even prepare/update the database to hold such a field of data.
    """
    _classic_read = True
    _classic_write = True
    _auto_join = False
    _properties = False
    _type = 'unknown'
    _obj = None
    _multi = False
    _symbol_c = '%s'
    _symbol_f = _symbol_set
    _symbol_set = (_symbol_c, _symbol_f)
    _symbol_get = None
    _deprecated = False

    __slots__ = [
        'copy',                 # whether value is copied by BaseModel.copy()
        'string',
        'help',
        'required',
        'readonly',
        '_domain',
        '_context',
        'states',
        'priority',
        'change_default',
        'size',
        'ondelete',
        'translate',
        'select',
        'manual',
        'write',
        'read',
        'selectable',
        'group_operator',
        'groups',               # CSV list of ext IDs of groups
        'deprecated',           # Optional deprecation warning
        '_args',
        '_prefetch',
    ]

    def __init__(self, string='unknown', required=False, readonly=False, domain=[], context={}, states=None, priority=0, change_default=False, size=None, ondelete=None, translate=False, select=False, manual=False, **args):
        """

        The 'manual' keyword argument specifies if the field is a custom one.
        It corresponds to the 'state' column in ir_model_fields.

        """
        # add parameters and default values
        args['copy'] = args.get('copy', True)
        args['string'] = string
        args['help'] = args.get('help', '')
        args['required'] = required
        args['readonly'] = readonly
        args['_domain'] = domain
        args['_context'] = context
        args['states'] = states
        args['priority'] = priority
        args['change_default'] = change_default
        args['size'] = size
        args['ondelete'] = ondelete.lower() if ondelete else None
        args['translate'] = translate
        args['select'] = select
        args['manual'] = manual
        args['write'] = args.get('write', False)
        args['read'] = args.get('read', False)
        args['selectable'] = args.get('selectable', True)
        args['group_operator'] = args.get('group_operator', None)
        args['groups'] = args.get('groups', None)
        args['deprecated'] = args.get('deprecated', None)
        args['_prefetch'] = args.get('_prefetch', True)

        self._args = EMPTY_DICT
        for key, val in args.iteritems():
            setattr(self, key, val)

        # prefetch only if _classic_write, not deprecated and not manual
        if not self._classic_write or self.deprecated or self.manual:
            self._prefetch = False

    def __getattr__(self, name):
        """ Access a non-slot attribute. """
        if name == '_args':
            raise AttributeError(name)
        try:
            return self._args[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        """ Set a slot or non-slot attribute. """
        try:
            object.__setattr__(self, name, value)
        except AttributeError:
            if self._args:
                self._args[name] = value
            else:
                self._args = {name: value}     # replace EMPTY_DICT

    def __delattr__(self, name):
        """ Remove a non-slot attribute. """
        try:
            del self._args[name]
        except KeyError:
            raise AttributeError(name)

    def new(self, _computed_field=False, **args):
        """ Return a column like `self` with the given parameters; the parameter
            `_computed_field` tells whether the corresponding field is computed.
        """
        # memory optimization: reuse self whenever possible; you can reduce the
        # average memory usage per registry by 10 megabytes!
        column = type(self)(**args)
        return self if self.to_field_args() == column.to_field_args() else column

    def to_field(self):
        """ convert column `self` to a new-style field """
        from openerp.fields import Field
        return Field.by_type[self._type](origin=self, **self.to_field_args())

    def to_field_args(self):
        """ return a dictionary with all the arguments to pass to the field """
        base_items = [
            ('copy', self.copy),
            ('index', self.select),
            ('manual', self.manual),
            ('string', self.string),
            ('help', self.help),
            ('readonly', self.readonly),
            ('required', self.required),
            ('states', self.states),
            ('groups', self.groups),
            ('change_default', self.change_default),
            ('deprecated', self.deprecated),
        ]
        truthy_items = filter(itemgetter(1), [
            ('group_operator', self.group_operator),
            ('size', self.size),
            ('ondelete', self.ondelete),
            ('translate', self.translate),
            ('domain', self._domain),
            ('context', self._context),
        ])
        return dict(base_items + truthy_items + self._args.items())

    def restart(self):
        pass

    def set(self, cr, obj, id, name, value, user=None, context=None):
        cr.execute('update '+obj._table+' set '+name+'='+self._symbol_set[0]+' where id=%s', (self._symbol_set[1](value), id))

    def get(self, cr, obj, ids, name, user=None, offset=0, context=None, values=None):
        raise Exception(_('undefined get method !'))

    def search(self, cr, obj, args, name, value, offset=0, limit=None, uid=None, context=None):
        ids = obj.search(cr, uid, args+self._domain+[(name, 'ilike', value)], offset, limit, context=context)
        res = obj.read(cr, uid, ids, [name], context=context)
        return [x[name] for x in res]

    def as_display_name(self, cr, uid, obj, value, context=None):
        """Converts a field value to a suitable string representation for a record,
           e.g. when this field is used as ``rec_name``.

           :param obj: the ``BaseModel`` instance this column belongs to 
           :param value: a proper value as returned by :py:meth:`~openerp.orm.osv.BaseModel.read`
                         for this column
        """
        # delegated to class method, so a column type A can delegate
        # to a column type B. 
        return self._as_display_name(self, cr, uid, obj, value, context=None)

    @classmethod
    def _as_display_name(cls, field, cr, uid, obj, value, context=None):
        # This needs to be a class method, in case a column type A as to delegate
        # to a column type B.
        return tools.ustr(value)



class time(_column):
    _type = 'time'
    __slots__ = []



    @staticmethod
    def now(*args):
        """ Returns the current datetime in a format fit for being a
        default value to a ``datetime`` field.

        This method should be provided as is to the _defaults dict, it
        should not be called.
        """
        return DT.datetime.now().strftime(
            tools.DEFAULT_SERVER_DATETIME_FORMAT)

    @staticmethod
    def context_timestamp(cr, uid, timestamp, context=None):
        """Returns the given timestamp converted to the client's timezone.
           This method is *not* meant for use as a _defaults initializer,
           because datetime fields are automatically converted upon
           display on client side. For _defaults you :meth:`fields.datetime.now`
           should be used instead.

           :param datetime timestamp: naive datetime value (expressed in UTC)
                                      to be converted to the client timezone
           :param dict context: the 'tz' key in the context should give the
                                name of the User/Client timezone (otherwise
                                UTC is used)
           :rtype: datetime
           :return: timestamp converted to timezone-aware datetime in context
                    timezone
        """
        assert isinstance(timestamp, DT.datetime.now().time()), 'Datetime instance expected'
        if context and context.get('tz'):
            tz_name = context['tz']  
        else:
            registry = openerp.modules.registry.RegistryManager.get(cr.dbname)
            user = registry['res.users'].browse(cr, SUPERUSER_ID, uid)
            tz_name = user.tz
        utc_timestamp = pytz.utc.localize(timestamp, is_dst=False) # UTC = no DST
        if tz_name:
            try:
                context_tz = pytz.timezone(tz_name)
                return utc_timestamp.astimezone(context_tz)
            except Exception:
                _logger.debug("failed to compute context/client-specific timestamp, "
                              "using the UTC value",
                              exc_info=True)
        return utc_timestamp

    @classmethod
    def _as_display_name(cls, field, cr, uid, obj, value, context=None):
        value = datetime.context_timestamp(cr, uid, DT.datetime.strptime(value, tools.DEFAULT_SERVER_DATETIME_FORMAT), context=context)
        return tools.ustr(value.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT))
