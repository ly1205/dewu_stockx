# -*- coding: utf-8 -*-
"""
@Author: admin
@Function: xxx
"""
import sqlite3
import time_util
import re
import traceback

# db_file = 'D:\workspace2\python\my_spider_2022\dewu_stockx\du_stockx.db'
# db_file = 'D:\my_workspace\my_spider_2022\dewu_stockx\du_stockx.db'
db_file = 'du_stockx.db'


def create_table():
    """
    创建表
    :return:
    """
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('''CREATE TABLE t_goods(goods_code  CHAR(50)  NOT NULL, du_goods_id char(64),
     sx_short_desc, create_time int not null)''')
    "Table created successfully"
    conn.commit()
    conn.close()


def save_records(records, table):
    """
    批量保存字典形式的记录
    """
    conn = sqlite3.connect(db_file)
    for record in records:
        cols = ''
        vals = ''
        for col, val in record.items():
            if not val:
                continue
            cols += ',' + col
            val = str(val)
            # 处理sql中的特殊字符
            val = val.replace('"', '').replace('\'', '')
            vals += ', \'' + val + '\''
        sql = f'insert into {table}({cols[1:]}) values({vals[1:]})'
        c = conn.cursor()
        c.execute(sql)
    conn.commit()
    conn.close()


def save_one(record, table):
    conn = sqlite3.connect(db_file)
    cols = ''
    vals = ''
    for col, val in record.items():
        if not val:
            continue
        cols += ',' + col
        # 处理sql中的特殊字符
        if type(val) != str:
            val = str(val)
        val = val.replace('"', '').replace('\'', '')
        vals += ', \'' + val + '\''
    sql = f'insert into {table}({cols[1:]}) values({vals[1:]})'
    c = conn.cursor()
    c.execute(sql)
    conn.commit()
    conn.close()


def update_one(record, table, query):
    """
    用字典方式更新一条记录
    """
    conn = sqlite3.connect(db_file)
    updates = []
    # 拼接更新字段
    for col, val in record.items():
        if not val:
            continue
        # 处理sql中的特殊字符
        if type(val) != str:
            val = str(val)
        val = val.replace('"', '').replace('\'', '')
        # updates += ',' + col+'=\''+val+'\''
        updates.append(col+"='"+val+"'")
    # 拼接条件
    conditions = []
    for col, val in query.items():
        if not val:
            continue
        val = val.replace('"', '').replace('\'', '')
        conditions.append(col+"='"+val+"'")
    sql = f'update {table} set {",".join(updates)} where {" and ".join(conditions)}'
    c = conn.cursor()
    c.execute(sql)
    conn.commit()
    conn.close()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def _common_select_rows(sql, as_dict=False):
    conn = sqlite3.connect(db_file)
    if as_dict:
        conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute(sql)
    rows = c.fetchall()
    conn.close()
    return rows


def _common_update(sql):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute(sql)
    conn.commit()
    conn.close()


def select_goods_id_task(col_name, col_name_2=None):
    """
    获取需要抓取商品id的货号
    """
    sql = f"select goods_code from t_goods_code where {col_name} is null and del_flag != 1"
    if col_name_2:
        sql += f" and {col_name_2} is not null and {col_name_2} !='-1'"
    return _common_select_rows(sql)


def set_du_goods_id(code, goods_id):
    """
    设置产品id
    """
    sql = f"update t_goods_code set du_goods_id='{goods_id}' where goods_code='{code}'"
    _common_update(sql)


def set_stx_goods_id(code, goods_id):
    """
    设置产品id
    """
    sql = f"update t_goods_code set sx_short_desc='{goods_id}' where goods_code='{code}'"
    _common_update(sql)


def select_sku_price_task(plat_type):
    """
    获取需要抓取sku价格的产品id
    """
    # if 'du' == plat_type:
    #     sql = f"select goods_code, du_goods_id from t_goods_code where du_goods_id is not null and " \
    #           f" du_goods_id != '-1' and sx_short_desc != '-1' and (du_sku_price_time is null or " \
    #             f"du_sku_price_time < '{time_util.get_today_str()}')"
    # else:
    #     sql = f"select goods_code, sx_short_desc from t_goods_code where sx_short_desc is not null and " \
    #           f" sx_short_desc != '-1' and du_goods_id != '-1' and (sx_sku_price_time is null or " \
    #             f"sx_sku_price_time < '{time_util.get_today_str()}')"
    if 'du' == plat_type:
        sql = f"select goods_code, du_goods_id from t_goods_code where du_goods_id is not null and " \
              f" du_goods_id != '-1' and sx_short_desc != '-1' and du_sku_price_time is null"

    else:
        sql = f"select goods_code, sx_short_desc from t_goods_code where sx_short_desc is not null and " \
              f" sx_short_desc != '-1' and du_goods_id != '-1' and sx_sku_price_time is null "
    return _common_select_rows(sql)


def update_sku_price_time(code, plat_type, sx_size_map=None):
    """
    更新价格抓取时间
    """
    if 'du' == plat_type:
        sql = f"update t_goods_code set du_sku_price_time = '{time_util.get_now_str()}' where goods_code='{code}'"
    else:
        if not sx_size_map:
            sql = f"update t_goods_code set sx_sku_price_time = '{time_util.get_now_str()}' where goods_code='{code}'"
        else:
            sql = f"update t_goods_code set sx_sku_price_time = '{time_util.get_now_str()}', sx_size_map=" \
                  f"'{sx_size_map}' where goods_code='{code}'"
    _common_update(sql)


def select_goods_skus(page_no=1, page_size=15, du_price_col=None, search_cate=None,
                      stx_price_col=None, price_diff=None, price_diff_rate=None,
                      spider_date_du=None, spider_date_stx=None, price_diff_rate_divider=None):
    """
    获取首页需要的数据列表
    """
    if du_price_col and stx_price_col and (price_diff or price_diff_rate):
        sql = f"select g.goods_code, i.title, GROUP_CONCAT(p.sku_name, \',\') as sku_names, g.create_time, " \
              f"(p.{stx_price_col}-d.{du_price_col}) as price_diff, g.du_sku_price_time, g.sx_sku_price_time," \
              f" g.category from t_goods_code g join t_base_info_du i" \
              f" on(g.goods_code=i.code) join t_sku_price_stx p on(g.goods_code = p.code) join" \
              f" t_sku_price_du d on(d.code = p.code and d.sku_name=p.sku_name) where 1=1 and g.del_flag != 1 "
        if price_diff:
            if int(price_diff) >= 0:
                sql += f"and p.{stx_price_col}-d.{du_price_col} >= {price_diff} "
            else:
                sql += f"and p.{stx_price_col}-d.{du_price_col} < {price_diff} "
        if price_diff_rate:
            price_diff_rate = float(price_diff_rate)/100
            if price_diff_rate >= 0:
                if price_diff_rate_divider == 'stx':
                    sql += f"and (p.{stx_price_col}-d.{du_price_col})/p.{stx_price_col} >= {price_diff_rate} "
                else:
                    sql += f"and (p.{stx_price_col}-d.{du_price_col})/d.{du_price_col} >= {price_diff_rate} "
            else:
                if price_diff_rate_divider == 'stx':
                    sql += f"and (p.{stx_price_col}-d.{du_price_col})/p.{stx_price_col} < {price_diff_rate} "
                else:
                    sql += f"and (p.{stx_price_col}-d.{du_price_col})/d.{du_price_col} < {price_diff_rate} "
    else:
        sql = f"select g.goods_code, i.title, GROUP_CONCAT(p.sku_name, \',\') as sku_names, g.create_time, '-1',  " \
              f"g.du_sku_price_time, g.sx_sku_price_time, g.category from t_goods_code g left join t_base_info_du i" \
              f" on(g.goods_code=i.code)  left join t_sku_price_stx p on(g.goods_code = p.code) left join" \
              f" t_sku_price_du d on(d.code = p.code and d.sku_name=p.sku_name) where 1=1 and g.del_flag != 1" \
              f" and g.sx_short_desc != '-1' and g.du_goods_id != '-1' "
    if spider_date_du:
        sql += f"and g.du_sku_price_time > '{spider_date_du}'"
    if spider_date_stx:
        sql += f"and g.sx_sku_price_time > '{spider_date_stx}'"
    if search_cate:
        sql += f" and g.category='{search_cate}'"
    sql += " GROUP BY i.code"
    total = count_by_sql(sql)
    sql += f" order by g.create_time desc limit {(int(page_no)-1)*int(page_size)}, {page_size}"
    rows = _common_select_rows(sql)
    return rows, total


def count_by_sql(sql):
    """
    获取总条数
    """
    columns = re.findall('select (.*) from', sql)[0]
    _count_sql = sql.replace(columns, 'count(1)')
    # 聚合查询总条数特殊处理
    if 'GROUP BY' in _count_sql:
        _count_sql = 'select count(1) from ('+_count_sql+')'
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    cursor = c.execute(_count_sql)
    rows = list(cursor)
    conn.close()
    return rows[0][0]


def select_base_info(code):
    """
    查询详情页需要展示的基础信息
    """
    sql = 'select ifnull(d.title, \'-\'), ifnull(d.sale_date, \'-\'), ifnull(d.sale_price, \'-\'), ' \
          'ifnull(d.total_sale, \'-\'), ifnull(d.last_3d_sale, \'-\'), ifnull(d.last_7d_sale, \'-\'),' \
          'ifnull(s.title, \'-\'), ifnull(s.sale_date, \'-\'), ifnull(s.sale_price, \'-\'), ifnull(s.total_sale, \'-\')' \
          ',ifnull(s.last_3d_sale, \'-\'), ifnull(s.last_7d_sale, \'-\') from t_base_info_du d ' \
          'left join t_base_info_stx s on(d.code=s.code) where d.code=\'' + code + '\''
    rows = _common_select_rows(sql)
    if rows:
        return rows[0]
    else:
        return None


def select_order_spider_task(plat_type):
    """
    查询需要抓取订单记录的货号
    """
    if plat_type == 'du':
        sql = f"select du_goods_id, goods_code from t_goods_code where du_goods_id is not null and " \
              f" du_goods_id != '-1' and sx_short_desc != '-1'  and (du_order_spider_time is null " \
              f"or du_order_spider_time <  '{time_util.get_time_before(12)}')"
    else:
        sql = f"select b.uuid, g.goods_code, g.sx_size_map from t_goods_code g join t_base_info_stx b  " \
              f" on(g.goods_code=b.code) where b.uuid is not null and g.du_goods_id != '-1' and" \
              f" g.sx_short_desc != '-1' and (sx_order_spider_time is null " \
              f"or sx_order_spider_time < '{time_util.get_time_before(12)}') and sx_sku_price_time is not null "
    return _common_select_rows(sql)


def select_sku_price_list(code):
    """
    查询详情页需要的尺码价格列表
    """
    # 查询两张表中最大时间，取最小值
    # sql1 = 'select max(spider_time) from t_sku_price_du'
    # sql2 = 'select max(spider_time) from t_sku_price_stx'
    # r1 = _common_select_rows(sql1)
    # r2 = _common_select_rows(sql2)
    # max_time = min(r1[0][0], r2[0][0])
    sql = f"select d.code as code, d.sku_name as sku_name, ifnull(s.price_buy, '/') as price_buy, " \
          f"ifnull(s.sell_get_price, '') as sell_get_price, ifnull(s.price_sell, '/') as price_sell," \
          f"ifnull(s.want_get_price, '/') as want_get_price, ifnull(d.price_normal, '/') as price_normal, " \
          f"ifnull(d.price_normal_get, '/') as price_normal_get,ifnull(d.price_shan, '/') as price_shan, " \
          f"ifnull(d.price_shan_get, '/') as price_shan_get, ifnull(d.price_ji, '/') as price_ji, " \
          f"ifnull(d.price_ji_get, '/') as price_ji_get, ifnull(d.price_want, '/') as price_want, " \
          f"ifnull(d.price_want_get, '/') as price_want_get ,ifnull(price_oversea, '/') as price_oversea, " \
          f"ifnull(s.price_buy_get, '/') as price_buy_get, ifnull(s.spider_time, '/') as spider_time" \
          f" from t_sku_price_du d join t_sku_price_stx s on(d.sku_name=s.sku_name  " \
          f"and d.code=s.code) where d.code='{code}'"
          # f"and d.code=s.code) where d.code='{code}' and d.spider_time = '{max_time}' and s.spider_time = '{max_time}'"
    return _common_select_rows(sql, as_dict=True)


def update_order_spider_time(code, col):
    """
    更新价格抓取时间
    """
    sql = f"update t_goods_code set {col} = '{time_util.get_now_str()}' where goods_code='{code}'"
    _common_update(sql)


def select_config_dict():
    """
    查询配置参数
    """
    sql = 'select name, value from t_config'
    rows = _common_select_rows(sql)
    config_dict = {}
    for row in rows:
        config_dict[row[0]] = row[1]
    return config_dict


def select_sale_report_stx(goods_code, sku_name, day_before):
    """
    查询统计趋势图
    """
    sql = f"select goods_code, size, SUBSTR(order_time, 0, 11) as order_date, count(1), avg(price) " \
          f"from t_order_history_stx where goods_code = '{goods_code}' and size='{sku_name}'" \
          f" and order_time > '{day_before}' group by order_date, goods_code, size"
    return _common_select_rows(sql)


def select_sale_report_du(goods_code, sku_name, day_before):
    """
    查询统计趋势图
    """
    sql = f"select goods_code, size, SUBSTR(about_time, 0, 11) as order_date, count(1), avg(price/100)  " \
          f"from t_order_history_du where goods_code = '{goods_code}' and about_time is not null " \
          f"and size = '{sku_name}' and about_time >= '{day_before}' group by order_date, goods_code, size"
    return _common_select_rows(sql)


def select_monitors():
    """
    查询监控列表
    """
    sql = 'select * from t_monitor order by create_time desc'
    return _common_select_rows(sql, as_dict=True)


def select_monitor(row_id):
    """
    查询监控详情
    """
    sql = 'select * from t_monitor where id = ' + row_id
    return _common_select_rows(sql, as_dict=True)


def delete_monitor(row_id):
    """
    删除监控详情
    """
    sql = 'delete from t_monitor where id = ' + row_id
    return _common_update(sql)


def select_sku_size_by_code(codes):
    """
    获取货号对应的尺码
    """
    codes = "'" + "','".join(codes.split(',')) + "'"
    sql = f"select d.code, GROUP_CONCAT(d.sku_name, ',') from t_sku_price_du d join t_sku_price_stx s " \
          f"on(d.code=s.code and d.sku_name=s.sku_name) and d.code in({codes}) group by d.code"
    return _common_select_rows(sql)


def select_task_status(search_cate=None):
    """
    查询任务状态
    """
    sql0 = "select count(1) from t_goods_code where del_flag != 1"
    if search_cate:
        sql0 += f" and category = '{search_cate}'"
    total = _common_select_rows(sql0)[0][0]
    # 无效
    sql1 = "select count(1) from t_goods_code where (du_goods_id = '-1' or sx_short_desc = '-1') and del_flag != 1"
    if search_cate:
        sql1 += f" and category = '{search_cate}'"
    invalid_count = _common_select_rows(sql1)[0][0]
    # 已完成
    # sql2 = 'select count(1) from t_goods_code where du_sku_price_time is not null and sx_sku_price_time' \
    #        ' is not null and du_order_spider_time is not null and sx_order_spider_time is not null'
    sql2 = 'select count(1) from t_goods_code where du_sku_price_time is not null and sx_sku_price_time' \
           ' is not null and del_flag != 1'
    if search_cate:
        sql2 += f" and category = '{search_cate}'"
    finish_count = _common_select_rows(sql2)[0][0]
    return total, invalid_count, finish_count, total-invalid_count-finish_count


def select_task_codes(task_type):
    """
    获取无效货号
    """
    if 'invalid' == task_type:
        invalid_du = _common_select_rows("select goods_code from t_goods_code where du_goods_id = '-1' and del_flag!=1")
        invalid_stx = _common_select_rows("select goods_code from t_goods_code where sx_short_desc = '-1' and del_flag!=1")
        return {'invalid_du': [r[0] for r in invalid_du], 'invalid_stx': [r[0] for r in invalid_stx]}
    return None


def select_goods_by_codes(codes, id_col):
    codes = "('" + "','".join(codes.split(',')) + "')"
    sql = f"select goods_code, {id_col} from t_goods_code where goods_code in{codes}"
    return _common_select_rows(sql)


def delete_all():
    """
    清空所有数据
    :return:
    """
    sql = 'update t_goods_code set del_flag = 1'
    _common_update(sql)


def set_del_flag(codes, category=''):
    """
    设置删除标记
    :param codes:
    :param category:
    :return:
    """
    codes = "'" + "','".join(codes) + "'"
    sql = f"update t_goods_code set del_flag=0, category='{category}' where goods_code in({codes})"
    _common_update(sql)


def select_exist_codes(codes):
    codes = "'" + "','".join(codes) + "'"
    sql = f"select goods_code from t_goods_code where goods_code in({codes})"
    rows = _common_select_rows(sql)
    ret_codes = [r[0] for r in rows]
    return ret_codes


def select_category():
    sql = "select * from t_category"
    return _common_select_rows(sql, as_dict=True)


def select_codes_by_cate(cate_name):
    sql = f"select goods_code from t_goods_code where category = '{cate_name}' and del_flag != 1"
    return _common_select_rows(sql, as_dict=True)


def del_by_cate(cate_name):
    sql = f"delete from t_category where name = '{cate_name}'"
    sql2 = f"update t_goods_code set del_flag=1 where category='{cate_name}'"
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute(sql)
    c.execute(sql2)
    conn.commit()
    conn.close()


if __name__ == '__main__':
    # create_table()
    # select_sku_price_list('DC8874-100')
    # select_task_status()
    s = select_task_codes('invalid')
    print(s)
    pass
