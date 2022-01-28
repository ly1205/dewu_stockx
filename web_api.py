import json
import db_util
import time_util
from log_conf import logger
import dewu_api_v2
import stockx_api
import DuSpider
import StockxSpider


def import_goods_codes(txt):
    """
    导入货号
    """
    lines = txt.split('\n')
    records = []
    for code in lines:
        records.append({'goods_code': code, 'create_time': time_util.get_now_str()})
    db_util.save_records(records, 't_goods_code')
    logger.info('成功导入 %s 个货号', len(records))


# def get_base_info(code):
#     return db_util.select_base_info(code)

def query_detail_by_code(code, tech_fee_rate, fee_rate_stx, plat_types):
    """
    通过货号实时抓取数据
    :param code:
    :param fee_rate_stx:
    :param plat_types:
    :param tech_fee_rate: 技术服务费费率
    :return:
    """
    config_dict = db_util.select_config_dict()
    du_info = None
    du_detail = None
    if 'du' in plat_types:
        du_goods = dewu_api_v2.get_goods_by_code(code, stop_on_error=True)
        if du_goods is False:
            return {'code': 0, 'msg': '货号'+code+'在得物没有搜索到商品'}
        if type(du_goods) == str:
            return {'code': 0, 'msg': '得物：'+json.loads(du_goods).get('msg')}
        du_info = {
            'name': du_goods.get('title'),
            'sell_date': '/',
            'price': du_goods.get('price')/100,
            'sell_num': du_goods.get('soldNum'),
            'sell_num_3days': '/',
            'sell_num_7days': '/',
        }
        records, du_detail = DuSpider.parse_price_records(du_goods.get('spuId'), code, config_dict, cst_du_tech_money=float(tech_fee_rate))
        if '已拒绝' in du_detail or '验证码' in du_detail:
            return {'code': 0, 'msg': '得物：'+json.loads(du_detail).get('msg')}
    stx_info = None
    stx_detail = None
    if 'stx' in plat_types:
        stock_goods = stockx_api.get_goods_by_code(code, stop_on_error=True)
        if stock_goods is False:
            return {'code': 0, 'msg': '货号' + code + '在stockx没有搜索到商品'}
        if type(stock_goods) == str:
            return {'code': 0, 'msg': stock_goods}
        stx_info = {
            'name': stock_goods.get('title'),
            'sell_date': stock_goods.get('releaseDate'),
            'price': stock_goods.get('retailPrice'),
            'sell_num': stock_goods.get('market').get('deadstockSold'),
            'sell_num_3days': stock_goods.get('salesLast72Hours') if stock_goods.get('salesLast72Hours') else '/',
            'sell_num_7days': '/',
        }
        stx_detail = StockxSpider.parse_price_records(stock_goods.get('urlKey'), code, config_dict, cst_buy_fee_rate=fee_rate_stx)
    base_info = {
        'code': code,
        'du': du_info,
        'stx': stx_info
    }
    detail = {
        'du': records,
        'stx': stx_detail[0]
    }
    return {'code': 1, 'data': {'base_info': base_info, 'detail': detail}}


if __name__ == '__main__':
    query_detail_by_code('394055-101')
    # import_goods_codes('DD1503-101\nCW7104-601\nBQ6817-401\nBQ6817-301\n553558-034\n554725-132\n554724-500\nCT0979-101\nBQ6472-300\n575441-402\n553560-800')