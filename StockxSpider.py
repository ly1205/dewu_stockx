# -*- coding: utf-8 -*-
"""
@Author: admin
@Function: xxx
"""
import json
import time
from stockx_api import search2, sku_price_list, goods_detail, order_history, get_goods_by_code
from log_conf import logger
import db_util
import stock_parse_util
import time_util
import random
import threading


def spider_goods_id():
    """
    根据货号抓取产品id
    """
    while True:
        tasks = db_util.select_goods_id_task('sx_short_desc')
        if not tasks:
            logger.info('暂无新的货号')
            time.sleep(60)
            continue
        logger.info('有%s个新的货号需要采集id', len(tasks))
        for num in tasks:
            try:
                num = num[0]
                matched_product = get_goods_by_code(num)
                if not matched_product:
                    time.sleep(5)
                    db_util.set_stx_goods_id(num, '-1')
                    continue
                goods_id = matched_product.get('urlKey')
                db_util.set_stx_goods_id(num, goods_id)
                #顺便保存商品基础信息
                db_util.save_one({
                    'code': num,
                    'title': matched_product.get('title'),
                    'sale_date': matched_product.get('releaseDate'),
                    'sale_price': matched_product.get('retailPrice'),
                    # 'total_sale': matched_product.get('soldNum'),
                    'name': matched_product.get('name'),
                    'uuid': matched_product.get('uuid'),
                    'img': matched_product.get('media').get('thumbUrl')
                }, 't_base_info_stx')
                logger.info('****************  %s 成功保存商品id: %s ', num, goods_id)
                time.sleep(5)
            except Exception:
                logger.exception('stockx货号id:%s采集异常', num)
                time.sleep(15)
        time.sleep(60)


def spider_order_history():
    """
    订单记录采集
    """
    while True:
        try:
            tasks = db_util.select_order_spider_task('stx')
            if not tasks:
                logger.info('暂无新的货号需要采集订单记录')
                time.sleep(30)
                continue
            logger.info('有 %s 货号需要采集订单记录', len(tasks))
            for t in tasks:
                try:
                    goods_id = t[0]
                    goods_code = t[1]
                    size_map_str = t[2]
                    size_map = json.loads(size_map_str)
                    s = order_history(goods_id)
                    s = json.loads(s)
                    orders = s.get('ProductActivity')
                    if not orders:
                        logger.warning('没有订单记录：%s', goods_code)
                        time.sleep(5)
                        continue
                    records = []
                    for d in orders:
                        records.append({
                            'goods_code': goods_code,
                            'size': size_map.get(d.get('shoeSize')),
                            'price': d.get('amount'),
                            'chain_id': d.get('chainId'),
                            'order_time': time_util.fmt_us_time(d.get('createdAt')),
                            'spider_time': time_util.get_now_str(),
                        })
                    db_util.save_records(records, 't_order_history_stx')
                    db_util.update_order_spider_time(goods_code, 'sx_order_spider_time')
                    logger.info('成功采集并保存 %s 条订单记录', len(records))
                    time.sleep(5)
                except Exception:
                    logger.exception('订单记录采集异常')
                    time.sleep(30)
        except Exception:
            logger.exception('订单记录采集异常')
            time.sleep(30)


def spider_sku_price_by_codes(tasks):
    config_dict = db_util.select_config_dict()
    success_count = 0
    for t in tasks:
        try:
            goods_code = t[0]
            sx_short_desc = t[1]
            records, size_map = parse_price_records(sx_short_desc, goods_code, config_dict)
            if records == 403:
                return {'code': -1, 'msg': 'stockx: 拒绝访问，请重新更换cookie或稍后再试'}
            if not records:
                logger.warning('没有价格列表：%s', sx_short_desc)
            else:
                db_util.save_records(records, 't_sku_price_stx')
                logger.info('STX: 成功采集并保存 %s 条价格', len(records))
            if size_map:
                db_util.update_sku_price_time(goods_code, 'stx', sx_size_map=json.dumps(size_map))
            else:
                db_util.update_sku_price_time(goods_code, 'stx')
            success_count += 1
            time.sleep(random.uniform(1.5, 3.5))
        except Exception:
            logger.exception('价格列表抓取失败')
            time.sleep(30)
    return {'code': 1, 'msg': f'stockx:成功采集{success_count}条'}


def spider_sku_price():
    """
    价格列表抓取
    """
    while True:
        tasks = db_util.select_sku_price_task('stx')
        if not tasks:
            logger.info('暂无新的货号需要采集价格列表')
            time.sleep(30)
            continue
        logger.info('有 %s 个货号需要采集价格列表', len(tasks))
        spider_sku_price_by_codes(tasks)
        time.sleep(60)


def parse_price_records(sx_short_desc, goods_code, config_dict, cst_buy_fee_rate=None):
    # 交易费率
    stx_trade_money_rate = config_dict.get('stx_trade_money_rate')
    # 转账手续费率
    stx_transfer_money_rate = config_dict.get('stx_transfer_money_rate')
    # 人民币美元汇率
    exchange_rate_rmb_dollar = config_dict.get('exchange_rate_rmb_dollar')
    # 购买手续费
    stx_buy_fee_rate = config_dict.get('stx_buy_fee_rate')
    # 优先使用自定义手续费率
    if cst_buy_fee_rate:
        stx_buy_fee_rate = cst_buy_fee_rate
    # 购买运费
    stx_postage_money = config_dict.get('stx_postage_money')
    if not stx_transfer_money_rate or not stx_trade_money_rate or not exchange_rate_rmb_dollar or \
            not stx_buy_fee_rate or not stx_postage_money:
        logger.error('请先设置交易费率|转账手续费率|汇率 !!!!!!!!!!!!!!!!!')
        return None, None
    stx_trade_money_rate = float(stx_trade_money_rate) / 100
    stx_transfer_money_rate = float(stx_transfer_money_rate) / 100
    exchange_rate_rmb_dollar = float(exchange_rate_rmb_dollar)
    stx_buy_fee_rate = float(stx_buy_fee_rate) / 100
    stx_postage_money = float(stx_postage_money)
    records = []
    htm = goods_detail(sx_short_desc)
    # 解析详情，获取购买价格信息
    if '<title>Access to this page has been denied.</title>' in htm:
        logger.warning('拒绝访问！！！！')
        # time.sleep(10)
        return 403, None
    detail = stock_parse_util.parse_detail(htm)
    if not detail:
        return None, None
    product_info = detail.get('Product')
    if not product_info:
        logger.warning('没有产品详情信息：%s', sx_short_desc)
        return None, None
    brand = product_info.get('brand')
    offers = detail.get('Product').get('offers').get('offers')
    if not offers:
        offers = [detail.get('Product').get('offers')]
    if not offers:
        logger.warning('没有尺码表')
        return None, None
    # 尺码转换
    size_map = stock_parse_util.parse_size_map(htm, 'eu', brand=brand, goods_name=product_info.get('name'))
    if not size_map:
        logger.warning('%s 没有尺码表', sx_short_desc)
        time.sleep(15)
        return None, None
    # 解析尺码出售价格
    sell_price_map = stock_parse_util.parse_sell_price_map(htm)
    for offer in offers:
        sku_id = offer.get('sku')
        # 获取出售价
        sell_price = sell_price_map.get(sku_id)
        sku_name = size_map.get(offer.get('description'))
        if not sku_name:
            # logger.warning('没有尺码对照表:%s', offer.get('description'))
            continue
        # stx普通出售到手价 = (Stockx 购买价-Stockx 购买价 * （①【卖出】交易费用+②【卖出】转账手续费))  *汇率
        price_buy = offer.get('price')
        sell_get_price = None
        price_buy_get = None
        if price_buy:
            # 普通出售到手价
            sell_get_price = (price_buy - price_buy * (stx_trade_money_rate + stx_transfer_money_rate)
                              ) * exchange_rate_rmb_dollar
            sell_get_price = round(sell_get_price, 2)
            #   普通购买到手价 = (Stockx 购买价+(Stockx 购买价*③【购买】手续费)+④【购买】运费)*汇率
            price_buy_get = (price_buy + (price_buy * stx_buy_fee_rate) + stx_postage_money) * exchange_rate_rmb_dollar
            price_buy_get = round(price_buy_get, 2)
        # stx 求购到手价 = （Stockx 求购价- Stockx 求购价*（①【卖出】交易费用+②【卖出】转账手续费))*汇率
        want_get_price = None
        if sell_price:
            want_get_price = (sell_price - sell_price * (stx_trade_money_rate + stx_transfer_money_rate)
                              ) * exchange_rate_rmb_dollar
            want_get_price = round(want_get_price, 2)
        records.append({
            'code': goods_code,
            # 购买价
            'price_buy': price_buy,
            # 尺码转换
            'sku_name': sku_name,
            # 求购价
            'price_sell': sell_price,
            # 出售到手价
            'sell_get_price': sell_get_price,
            # 求购到手价
            'want_get_price': want_get_price,
            # 购买到手价
            'price_buy_get': price_buy_get,
            'spider_time': time_util.get_now_str()
        })
    return records, size_map


if __name__ == '__main__':
    # spider_goods_id()
    threading.Thread(target=spider_goods_id, name='stockx货号id采集').start()
    # spider_sku_price()
    threading.Thread(target=spider_sku_price, name='stockx价格列表采集').start()
    # threading.Thread(target=spider_order_history, name='stockx订单记录采集').start()