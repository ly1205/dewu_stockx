# -*- coding: utf-8 -*-
"""
@Author: admin
@Function: xxx
"""
import json
import time
from dewu_api_v2 import search, sku_price_list, goods_detail, \
    sku_price_info, last_sold_list, view_buyer, get_goods_by_code
from log_conf import logger
import db_util
import time_util
import threading
import random
import re

stock_numbers = ['DD1503-101', 'CW7104-601', 'BQ6817-401', 'BQ6817-301', '553558-034', '554725-132', '554724-500', 'CT0979-101', 'BQ6472-300', '575441-402', '553560-800', '554724-133', 'DD1666-100', 'CW6576-800', 'BQ6817-700', 'BQ6817-302', 'DD8386-001', 'CD7782-107', 'CW1590-104', 'CD0461-002', 'DD1869-103', 'DJ4699-100', 'CT8527-100', 'DB2179-102', 'DD1399-102', 'DD1869-104', 'DD1391-102', 'CW1590-103', 'CW1590-102', 'DD1391-101', 'CW1590-700', 'DD1391-700', '575441-035', '555088-035', 'DD1869-102', 'CV9844-600', 'CT8527-400', '408452-400', 'CW1590-001', 'CW1590-002', 'DD1503-105', 'DD1503-103', 'DD1399-101', 'DD1503-102', 'DD1503-100', 'DB3610-105', 'CT0979-602', 'CZ4385-016', 'CD0461-001', 'DJ6249-200', 'DB0732-200', '575441-134', '555088-134', 'DB2179-100', 'CW1590-100', 'CZ0175-003', 'DD1391-100', 'DB2179-101', 'DD1399-100', 'DD1391-002', 'DD1391-001', 'DD1649-001', 'DD2192-001', '554725-500', 'BQ6472-500', 'BQ6472-202', 'BQ6472-102', 'DC0774-105', 'CZ0774-300', '553560-030', '553560-040', '553560-034', '553558-030', '553558-144', 'DM5447-111', 'DD1525-100', 'DD1525-001', 'DC3584-100', 'DC3584-001', 'DC3584-200', 'DJ9158-200', 'DM6435-222', 'CI0919-110', 'CI0919-108', 'CI0919-109', 'CI0919-111', 'CI0919-700', 'CI0919-003', 'CI0919-112', 'CI0919-103', 'DO7449-111', 'DM8462-400', 'CW2288-111', 'CW2288-001', 'DD8959-100', 'DD8959-001', '366731-100', 'DD9625-100', 'DO6634-100', 'DM9473-100', 'DM8154-100', 'DD1523-100', 'DD1523-500', 'BV0740-100', 'CK6649-702', 'CK6649-104', 'CK6649-105', 'DM5441-001', 'CV1758-100', 'DA8301-100', 'DC8891-001', 'AT4144-601', 'AT4144-100', 'CJ9179-200', 'CK0262-700', 'DO7450-511', 'DO7450-211', 'CZ0270-102', 'DH2920-111', 'DB4542-100', 'DM5036-100', 'DO5220-141', 'DO5220-161', 'DO5220-131', 'CW2289-111', 'DC8874-101', 'DC8874-100', 'DO2333-101', 'DC8873-101', 'DO5215-331', 'DA7024-600', 'DA7024-601', 'DA7024-200', 'DA7024-101', 'DO2330-511', 'DA8571-200', 'DO3809-100', 'DO3809-101']


def spider_goods_id():
    """
    根据货号抓取产品id
    """
    success_count = 0
    while True:
        tasks = db_util.select_goods_id_task('du_goods_id', col_name_2='sx_short_desc')
        if not tasks:
            logger.info('暂无新的货号...')
            time.sleep(60)
            continue
        logger.info('有%s个新的货号需要采集id', len(tasks))
        for num in tasks:
            try:
                num = num[0]
                matched_product = get_goods_by_code(num)
                if not matched_product:
                    logger.warning('货号 %s 未搜索到商品！！！', num)
                    db_util.set_du_goods_id(num, '-1')
                    time.sleep(15)
                    continue
                goods_id = matched_product.get('productId')
                db_util.set_du_goods_id(num, goods_id)
                #顺便保存商品基础信息
                db_util.save_one({
                    'code': num,
                    'title': matched_product.get('title'),
                    'sub_title': matched_product.get('subTitle'),
                    'img': matched_product.get('logoUrl'),
                    'total_sale': matched_product.get('soldNum')
                }, 't_base_info_du')
                logger.info('****************  %s 成功保存商品id: %s ', num, goods_id)
                success_count += 1
                if success_count < 20:
                    time.sleep(random.uniform(1.5, 5.5))
                else:
                    logger.warning('连续超过20个，暂停5分钟...')
                    success_count = 0
                    time.sleep(300)
            except Exception:
                logger.exception('货号id采集异常')
                time.sleep(15)
        time.sleep(60)


def spider_sku_price_by_codes(tasks):
    config_dict = db_util.select_config_dict()
    success_count = 0
    for task in tasks:
        try:
            goods_id = task[1]
            goods_code = task[0]
            records, detail = parse_price_records(goods_id, goods_code, config_dict)
            if '请求已拒绝' in detail or '校验验证码' in detail:
                logger.warning(detail)
                # time.sleep(300)
                return {'code': -1, 'msg': '得物：' + detail + f'(已成功{success_count}个)'}
            db_util.save_records(records, 't_sku_price_du')
            db_util.update_sku_price_time(goods_code, 'du')
            logger.info('DU: %s 价格列表抓取并保存成功', goods_code)
            detail = json.loads(detail)
            data = detail.get('data')
            d = data.get('detail')
            last_sold = data.get('lastSold')
            base_info = {
                'code': goods_code,
                'sale_date': d.get('sellDate'),
                'sale_price': d.get('authPrice'),
                'total_sale': last_sold.get('count'),
                'title': d.get('title'),
                'sub_title': d.get('subTitle'),
                'img': d.get('logoUrl'),
            }
            db_util.save_one(base_info, 't_base_info_du')
            # logger.info('%s 更新基础信息成功', goods_id)
            success_count += 1
            if success_count < 20:
                time.sleep(random.uniform(1.5, 5.5))
            else:
                logger.warning('连续超过20个，暂停5分钟...')
                success_count = 0
                time.sleep(300)
        except Exception:
            logger.exception('sku价格列表获取异常, %s', task)
            time.sleep(15)
    return {'code': 1, 'msg': f'得物：成功采集{success_count}条'}


def spider_sku_price():
    """
    抓取不同尺码的价格
    """
    while True:
        tasks = db_util.select_sku_price_task('du')
        if not tasks:
            logger.info('暂无需要采集价格列表的货号...')
            time.sleep(30)
            continue
        logger.info('共 %s 个商品需要抓取价格列表', len(tasks))
        spider_sku_price_by_codes(tasks)
        time.sleep(60)


def parse_price_records(goods_id, goods_code, config_dict, cst_du_tech_money=None):
    """
    解析不同尺码价格
    """
    # du技术服务费率（%）
    if cst_du_tech_money:
        du_tech_money = cst_du_tech_money
    else:
        du_tech_money = config_dict.get('du_tech_money')
    # du转账服务费率（%）
    du_transfer_money = config_dict.get('du_transfer_money')
    # du查验费（元）
    du_check_money = config_dict.get('du_check_money')
    # du鉴别（元）
    du_discern_money = config_dict.get('du_discern_money')
    # du包装服务费（元）
    du_pkg_money = config_dict.get('du_pkg_money')
    if not du_tech_money or not du_transfer_money or not du_check_money or not du_discern_money or not du_pkg_money:
        logger.error('请先设置配置参数')
        return None, None
    du_tech_money = float(du_tech_money) / 100
    du_transfer_money = float(du_transfer_money) / 100
    # ①技术服务费率+②转账服务费率
    other_fee1 = du_tech_money + du_transfer_money
    # ③查验费+④鉴别费+⑤包装服务费
    other_fee2 = float(du_check_money) + float(du_discern_money) + float(du_pkg_money)
    detail = goods_detail(goods_id, _proxy=None, stop_on_error=True)
    if '校验验证码' in detail or '请求已拒绝' in detail:
        return None, detail
    price_list = sku_price_list(goods_id, proxy=None, stop_on_error=True)
    if '校验验证码' in price_list or '请求已拒绝' in price_list:
        return None, price_list
    sku_price_infos = sku_price_info(detail, price_list)
    want_buy_price = {}
    if not cst_du_tech_money:
        want_buy_price = get_want_buy_price(goods_id)
    records = []
    for price in sku_price_infos:
        sku_name = price.get('sku_name')
        trade_info_list = price.get('tradeChannelInfoList')
        trade_price_dict = {}
        for trade_info in trade_info_list:
            origin_price = trade_info.get('finalPrice')
            if not origin_price:
                origin_price = trade_info.get('price')
            trade_price_dict[trade_info.get('tradeDesc')] = origin_price / 100
        # 得物 卖普通价到手 = 得物 普通价-（得物 普通价*（①技术服务费+②转账服务费））-③查验费-④鉴别费-⑤包装服务费
        price_normal = trade_price_dict.get('普通发货')
        price_normal_get = None
        if price_normal:
            price_normal_get = round(price_normal - (price_normal * other_fee1) - other_fee2, 2)
        # 得物 卖闪电到手价 = 得物 闪电价-（得物 闪电价*（①技术服务费+②转账服务费））-③查验费-④鉴别费-⑤包装服务费
        price_shan = trade_price_dict.get('闪电直发')
        price_shan_get = None
        if price_shan:
            price_shan_get = round(price_shan - (price_shan * other_fee1) - other_fee2, 2)
        # 极速到手价 = 得物 极速价-（得物 极速价*（①技术服务费+②转账服务费））-③查验费-④鉴别费-⑤包装服务费
        price_ji = trade_price_dict.get('极速发货')
        price_ji_get = None
        if price_ji:
            price_ji_get = round(price_ji - (price_ji * other_fee1) - other_fee2, 2)
        # 求购到手价 = 得物 求购价-(得物 求购价*（①技术服务费+②转账服务费））-③查验费-④鉴别费-⑤包装服务费
        price_want = want_buy_price.get(sku_name)
        price_want_get = None
        if price_want:
            price_want_get = round(price_want - (price_want * other_fee1) - other_fee2, 2)
        price_oversea = trade_price_dict.get('香港直邮')
        records.append({
            'code': goods_code,
            'sku_name': sku_name,
            'price_normal': price_normal,
            'price_normal_get': price_normal_get,
            'price_shan': price_shan,
            'price_shan_get': price_shan_get,
            'price_ji': price_ji,
            'price_ji_get': price_ji_get,
            'price_oversea': price_oversea,
            'price_want': price_want,
            'price_want_get': price_want_get,
            'spider_time': time_util.get_now_str()
        })
    return records, detail


def get_want_buy_price(spu_id):
    """
    获取求购价
    """
    try:
        s = view_buyer(spu_id)
        s = json.loads(s)
        max_price_list = s.get('data').get('skuMaxPriceDtoList')
        if not max_price_list:
            logger.warning('%s 求购价获取失败:%s', spu_id, s)
            return {}
        price_dict = {}
        for p in max_price_list:
            price = p.get('price')
            if not price:
                continue
            price_dict[p.get('skuSaleProp')] = price/100
        return price_dict
    except Exception:
        logger.exception('求购价获取异常: %s', spu_id)
        return {}


def spider_order_history():
    while True:
        try:
            tasks = db_util.select_order_spider_task('du')
            if not tasks:
                logger.info('暂无需要抓取订单的货号')
                time.sleep(60)
                continue
            logger.info('有%s 个货号需要抓取订单记录', len(tasks))
            for t in tasks:
                goods_id = t[0]
                goods_code = t[1]
                s = last_sold_list(goods_id, _proxy=None)
                s = json.loads(s)
                order_list = s.get('data').get('list')
                records = []
                for order in order_list:
                    fmt_time = order.get('formatTime')
                    # 根据返回的时间***分钟/小时/天 前，估算下单时间，用于统计分析
                    about_time = ''
                    time_num = re.findall('(\\d+)', fmt_time)
                    if time_num:
                        time_num = int(time_num[0])
                        if '分钟' in fmt_time:
                            about_time = time_util.get_time_before(minutes=time_num)
                        elif '小时' in fmt_time:
                            about_time = time_util.get_time_before(hours=time_num)
                        elif '天' in fmt_time:
                            about_time = time_util.get_time_before(days=time_num)
                        elif '刚刚' in fmt_time:
                            about_time = time_util.get_now_str()
                        else:
                            logger.warning('非预期下单时间：%s', fmt_time)
                    else:
                        logger.warning('非预期下单时间：%s', fmt_time)
                    records.append({
                        'goods_code': goods_code,
                        'size': order.get('propertiesValues'),
                        'buyer_name': order.get('userName'),
                        'price': order.get('price'),
                        'avatar': order.get('avatar'),
                        'format_time': fmt_time,
                        'about_time': about_time,
                        'spider_time': time_util.get_now_str()
                    })
                db_util.save_records(records, 't_order_history_du')
                # 更新订单抓取时间
                db_util.update_order_spider_time(goods_code, 'du_order_spider_time')
                logger.info('货号：%s，成功采集并保存 %s 条订单记录', goods_code, len(records))
                time.sleep(random.uniform(3.5, 13.5))
        except Exception:
            logger.exception('抓取订单记录失败')


if __name__ == '__main__':
    # spider_goods_id()
    # spider_sku_price()
    threading.Thread(target=spider_goods_id, name='du货号id采集').start()
    threading.Thread(target=spider_sku_price, name='du价格列表采集').start()
    # threading.Thread(target=spider_order_history, name='du订单记录采集').start()

