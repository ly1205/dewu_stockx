# -*- coding: utf-8 -*-
"""
@Author: admin
@Function: xxx
"""
import re
import json


def parse_detail(htm):
    """
    解析产品详情
    """
    details = re.findall('<script type="application/ld\\+json">(.*?)</script>', htm)
    if not details:
        return None
    result_dict = {}
    for detail_str in details:
        info = json.loads(detail_str)
        result_dict[info.get('@type')] = info
    return result_dict


def parse_size_map(htm, target_type, brand='', goods_name=''):
    """
    解析尺码对照表
    """
    # Nike 自定义尺码
    if brand in ['Nike', 'Jordan'] or 'nike' in brand or 'jordan' in brand:
        return {
            '3.5': '35.5',
            '4': '36',
            '4.5': '36.5',
            '5': '37.5',
            '5.5': '38',
            '6': '38.5',
            '6.5': '39',
            '7': '40',
            '7.5': '40.5',
            '8': '41',
            '8.5': '42',
            '9': '42.5',
            '9.5': '43',
            '10': '44',
            '10.5': '44.5',
            '11': '45',
            '11.5': '45.5',
            '12': '46',
            '12.5': '46.5',
            '13': '47.5',
            '14': '48',
            '15': '48.5',
            '5W': '35.5',
            '5.5W': '36',
            '6W': '36.5',
            '6.5W': '37.5',
            '7W': '38',
            '7.5W': '38.5',
            '8W': '39',
            '8.5W': '40',
            '9W': '40.5',
            '9.5W': '41',
            '10W': '42',
            '10.5W': '42.5',
            '11W': '43',
            '11.5W': '44',
            '12W': '44.5',
            '12.5W': '45',
            '3.5Y': '35.5',
            '4Y': '36',
            '4.5Y': '36.5',
            '5Y': '37.5',
            '5.5Y': '38',
            '6Y': '38.5',
            '6.5Y': '39',
            '7Y': '40',
            '0C': '15',
            '1C': '16',
            '2C': '17',
            '3C': '18.5',
            '4C': '19.5',
            '5C': '21',
            '6C': '22',
            '7C': '23.5',
            '8C': '25',
            '9C': '26',
            '10C': '27',
            '10.5C': '27.5',
            '11C': '28',
            '11.5C': '28.5',
            '12C': '29.5',
            '12.5C': '30',
            '13C': '31',
            '13.5C': '31.5',
            '1Y': '32',
            '1.5Y': '33',
            '2Y': '33.5',
            '2.5Y': '34',
            '3Y': '35',
            '3.5Y': '35.5',
        }
    # 阿迪达斯区分是不是拖鞋
    if brand == 'adidas' or 'adidas' in brand:
        # 拖鞋
        if 'Slide' in goods_name:
            return {
                '4': '36.5',
                '5': '38',
                '6': '39',
                '7': '40.5',
                '8': '42',
                '9': '43',
                '10': '44.5',
                '11': '46',
                '12': '47',
                '13': '48.5'
            }
        return {
            '4': '36',
            '4.5': '36.5',
            '5': '37',
            '5.5': '38',
            '6': '38.5',
            '6.5': '39',
            '7': '40',
            '7.5': '40.5',
            '8': '41',
            '8.5': '42',
            '9': '42.5',
            '9.5': '43',
            '10': '44',
            '10.5': '44.5',
            '11': '45',
            '11.5': '45.5',
            '12': '46',
            '12.5': '46.5',
            '13': '47',
            '14': '48'
        }
    results = re.findall('window.__APOLLO_STATE__ = (.*)', htm)
    if results:
        results = results[0]
        s = json.loads(results[0: len(results)-1])
        size_map = {}
        for k in s.keys():
            if not k.startswith('Variant:'):
                continue
            size_chart = s.get(k).get('sizeChart')
            display_options = size_chart.get('displayOptions')
            for option in display_options:
                if target_type == option.get('type'):
                    size_map[size_chart.get('baseSize')] = option.get('size').replace(target_type.upper()+' ', '')
                    break
        return size_map
    return {}


def parse_sell_price_map(htm):
    """
    解析尺码对照表
    """
    results = re.findall('window.__APOLLO_STATE__ = (.*)', htm)
    if results:
        results = results[0]
        s = json.loads(results[0: len(results)-1])
        price_map = {}
        for k in s.keys():
            if not k.startswith('Variant:'):
                continue
            item = s.get(k)
            v_id = item.get('id')
            market = item.get('market({\"currencyCode\":\"USD\"})')
            bid_ask_data = market.get('bidAskData({\"country\":\"CN\"})')
            # price_map[v_id] = bid_ask_data.get('highestBid')
            price_map[v_id] = bid_ask_data.get('lowestAsk')
        return price_map
    return {}
