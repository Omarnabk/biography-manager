import time
import uuid

from config import ALLOWED_PHOTO_EXTENSIONS


def allowed_photo_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PHOTO_EXTENSIONS


def str2list(input_str):
    if input_str is None:
        return []
    return input_str.split(';')


def list2str(input_list):
    if input_list is None:
        return ''
    return ';'.join(input_list)


def sqlite_select(conn, table, cols, conds=dict(), sort_by=str()):
    if conds:
        if len(conds) > 1:
            where_cond = ' AND '.join(f'LOWER({cond})=LOWER(:{cond})' for cond in conds.keys())
        else:
            where_cond = ' '.join(f'LOWER({cond})=LOWER(:{cond})' for cond in conds.keys())
    else:
        where_cond = ' 1=1 '

    sql = f'SELECT {", ".join(cols)} FROM {table} WHERE {where_cond}'

    if sort_by:
        sql = sql + f' order by {sort_by} DESC '
    result = conn.cursor().execute(sql, conds)
    return get_list_of_dict(keys=cols, list_of_tuples=result)


def sqlite_insert(conn, table, rows, replace_existing=False):
    cols = ', '.join('"{}"'.format(col) for col in rows.keys())
    vals = ', '.join(':{}'.format(col) for col in rows.keys())
    replace = ''
    if replace_existing:
        replace = 'OR REPLACE'
    sql = f'INSERT {replace} INTO "{table}" ({cols}) VALUES ({vals})'

    affected_rows = conn.cursor().execute(sql, rows)
    conn.commit()
    return affected_rows.rowcount


def sqlite_update(conn, table, rows, conds):
    vals = ', '.join(f'{col}=:{col}' for col in rows.keys())
    where_cond = ', '.join(f'LOWER({cond})=LOWER(:{cond})' for cond in conds.keys())
    sql = f'UPDATE  "{table}" SET {vals} WHERE {where_cond}'

    affected_rows = conn.cursor().execute(sql, {**rows, **conds})
    conn.commit()
    return affected_rows.rowcount


def sqlite_delete(conn, table, conds):
    where_cond = ', '.join(f'LOWER({cond})=LOWER(:{cond})' for cond in conds.keys())
    sql = f'DELETE FROM {table} WHERE {where_cond}'
    affected_rows = conn.cursor().execute(sql, conds)
    conn.commit()
    return affected_rows.rowcount


def get_list_of_dict(keys, list_of_tuples):
    """
    This function will accept keys and list_of_tuples as args and return list of dicts
    """
    list_of_dict = [dict(zip(keys, values)) for values in list_of_tuples]
    return list_of_dict


def generate_id(key):
    return uuid.uuid5(uuid.NAMESPACE_DNS, str(key) + str(time.time())).hex


def form_response(data, error_msg='', success_msg=''):
    return {
        'data': data,
        'error_msg': error_msg,
        'success_msg': success_msg
    }
