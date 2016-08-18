

from openerp.models import BaseModel

from openerp import api
import pytz
import babel.dates
import dateutil.relativedelta
import datetime
import dateutil
@api.model
def my_read_group_process_groupby(self, gb, query):
    """
        Helper method to collect important information about groupbys: raw
        field name, type, time information, qualified name, ...
    """
    split = gb.split(':')
    field_type = self._fields[split[0]].type
    gb_function = split[1] if len(split) == 2 else None
    temporal = field_type in ('date', 'datetime')
    tz_convert = field_type == 'datetime' and self._context.get('tz') in pytz.all_timezones
    qualified_field = self._inherits_join_calc(self._table, split[0], query)
    if temporal:
        display_formats = {
            # Careful with week/year formats:
            #  - yyyy (lower) must always be used, *except* for week+year formats
            #  - YYYY (upper) must always be used for week+year format
            #         e.g. 2006-01-01 is W52 2005 in some locales (de_DE),
            #                         and W1 2006 for others
            #
            # Mixing both formats, e.g. 'MMM YYYY' would yield wrong results,
            # such as 2006-01-01 being formatted as "January 2005" in some locales.
            # Cfr: http://babel.pocoo.org/docs/dates/#date-fields
            'day': 'dd MMM yyyy', # yyyy = normal year
            'week': "'W'w YYYY",  # w YYYY = ISO week-year
            'month': 'MMMM yyyy',
            'quarter': 'QQQ yyyy',
            'year': 'yyyy',
            'hour' : 'dd MMM yyyy HH mm SS',
        }
        time_intervals = {
            'day': dateutil.relativedelta.relativedelta(days=1),
            'day': dateutil.relativedelta.relativedelta(days=1),
            'hour': dateutil.relativedelta.relativedelta(days=1,hours=1),
            'halfday': dateutil.relativedelta.relativedelta(days=1,hours=12),
            'week': datetime.timedelta(days=7),
            'twoweeks': datetime.timedelta(days=14),
            'halfmonth':datetime.timedelta(days=15),
            'month': dateutil.relativedelta.relativedelta(months=1),
            'quarter': dateutil.relativedelta.relativedelta(months=3),
            'half': dateutil.relativedelta.relativedelta(months=6),
            'year': dateutil.relativedelta.relativedelta(years=1)
        }
        if tz_convert:
            qualified_field = "timezone('%s', timezone('UTC',%s))" % (self._context.get('tz', 'UTC'), qualified_field)
        qualified_field = "date_trunc('%s', %s)" % (gb_function or 'month', qualified_field)
    if field_type == 'boolean':
        qualified_field = "coalesce(%s,false)" % qualified_field
    return {
        'field': split[0],
        'groupby': gb,
        'type': field_type, 
        'display_format': display_formats[gb_function or 'month'] if temporal else None,
        'interval': time_intervals[gb_function or 'month'] if temporal else None,                
        'tz_convert': tz_convert,
        'qualified_field': qualified_field
    }
def my_read_group_format_result(self, data, annotated_groupbys, groupby, groupby_dict, domain, context):
    """
        Helper method to format the data contained in the dictionary data by 
        adding the domain corresponding to its values, the groupbys in the 
        context and by properly formatting the date/datetime values. 
    """
    domain_group = [dom for gb in annotated_groupbys for dom in self._read_group_get_domain(gb, data[gb['groupby']])]
    for k,v in data.iteritems():
        gb = groupby_dict.get(k)
        if gb and gb['type'] in ('date') and v:
            data[k] = babel.dates.format_date(v, format=gb['display_format'], locale=context.get('lang', 'en_US'))
        if gb and gb['type'] in ('datetime') and v:
            data[k] = babel.dates.format_datetime(v, format=gb['display_format'], locale=context.get('lang', 'en_US'))

    data['__domain'] = domain_group + domain 
    if len(groupby) - len(annotated_groupbys) >= 1:
        data['__context'] = { 'group_by': groupby[len(annotated_groupbys):]}
    del data['id']
    return data
BaseModel._read_group_process_groupby = my_read_group_process_groupby
BaseModel._read_group_format_result = my_read_group_format_result
