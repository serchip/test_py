"""
pgsql.py
====================================
Вспомагательные функции для построения SQL postgres
"""
from typing import Union, Tuple, List

class PGsqlOrderByExcept(Exception):
    pass


def _quote_ident(ident):
    return '"{}"'.format(ident.replace('"', '""'))


def _quote_literal(string):
    return "'{}'".format(string.replace("'", "''"))


def quote(field_value) -> str:
    """Escape a value to be able to insert into PostgreSQL
    :param field_value:
    :return:
    """
    if isinstance(field_value, str):
        return _quote_literal(field_value)
    if field_value is None:
        return 'NULL'
    if isinstance(field_value, (int, float, complex)):
        return str(field_value)
    # Applicable for date, time, text, varchar
    return _quote_literal(str(field_value))


def quote_array(values, wrap=True) -> str:
    """Convert Python value into string that is compatible with PostgreSQL's query
    first_name = "Name 01" => 'Name 01'
    this_date = datetime.datetime.now() => '2018-07-30 11:54:25.161946'
    this_date = datetime.datetime.now(datetime.timezone.utc) => '2018-07-30 05:12:30.279286+00:00'
    See: https://paquier.xyz/postgresql-2/manipulating-arrays-in-postgresql/
    :param list values:
    :param bool wrap:
    :return:
    """
    if wrap:
        ret = "'{%s}'"
    else:
        ret = "%s"
    quoted_values = []
    for v in values:
        quoted_values.append(quote(v))
    return ret % ",".join(quoted_values)

def generate_filter(field: str, value: Union[str, Tuple], op: Union[str, None]) -> str:
    """Функция генерит WHERE запрос для SQL
    Args:
        field: поле в таблице
        value: значение
        op: оператор
    Return:
        sql между WHERE и AND
    """

    and_list = []
    op = op or "="  # op can be None (default value)
    simple_ops = {
        "=": 1,
        ">": 2,
        ">=": 3,
        "<": 4,
        "<=": 5,
        "<>": 6,
        "!=": 7,
        "in": 8,
        "not in": 9,
        "between": 10,
        "contain": 11,
        "not contain": 12,
        "overlap": 13,
        "not overlap": 14,
        "like": 15
    }
    try:
        op_position = simple_ops[op]
    except IndexError:
        raise UserWarning("Bad operation: %s", op)
    if op_position < 8:
        if value.isdigit():
            return u"%s %s %d" % (field,  op, int(value))
        else:
            return u"%s %s %s" % (field, op, quote(value))
    if op_position < 9:
        return u"%s = ANY(%s)" % (field, quote_array(value))
    if op_position < 10:
        return u"%s != ALL(%s)" % (field, quote_array(value))
    if op_position < 11:
        return u"%s BETWEEN %s AND %s" % (field, quote(value[0]), quote(value[1]))
    if op_position < 12:
        # applicable for range field
        return u"%s @> %s" % (field, quote(value))
    if op_position < 13:
        # applicable for range field
        return u"NOT (%s @> %s)" % (field, quote(value))
    if op_position < 14:
        # applicable for range field
        # value must be a function: int4range, int8range, tsrange ...
        # https://www.postgresql.org/docs/10/static/rangetypes.html
        if not isinstance(value, str):
            raise UserWarning("Bad value compared against the field %s: string is required", field)
        if not "range(" in value:
            raise UserWarning("Bad value compared against the field %s: range function is required", field)
        return u"%s && %s" % (field, value.replace("'", ""))
    if op_position < 15:
        if not isinstance(value, str):
            raise UserWarning("Bad value compared against the field %s: string is required", field)
        if not "range(" in value:
            raise UserWarning("Bad value compared against the field %s: range function is required", field)
        return u"NOT (%s && %s)" % (field, value.replace("'", ""))
    else:
        # LIKE
        return u"%s LIKE %s" % (field, quote(value))

def generate_order_by(fields: List[str], sort_orders: List[str], table_pre: str = '') -> str:
    """Функция генерит ORDER BY запрос для SQL
    Args:
        fields: список полей для сортировки
        sort_orders: список (asc\desc) значений
        table_pre: префикс таблицы в запросе
    Return:
        sql ORBER BY
    """
    def _get_str_order(field: str, sort_order: str, table_pre: str = '') -> str:
        """Функция генерации одной FIELD ASC"""
        if sort_order.upper() not in ['ASC', 'DESC']:
            raise PGsqlOrderByExcept(f'sort_order value should consist of ASC or DESC but he {sort_order}')
        if table_pre:
            return f"{table_pre}.{field} {sort_order.upper()}"
        return f"{field} {sort_order.upper()}"

    if not fields:
        return ''
    orders_clause = []
    for i, f in enumerate(fields):
        orders_clause.append(_get_str_order(f, sort_orders[i], table_pre))
    return "ORDER BY " + ", ".join(orders_clause)
