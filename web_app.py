# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, jsonify, Response
import json
import os
import re
import time
import db_util
import requests
from log_conf import logger
import time_util
import web_api
import DuSpider
import StockxSpider
import stockx_api
import dewu_api_v2


app = Flask(__name__, template_folder='./')
base_uri = ''
@app.route(base_uri + '/<file>', methods=['GET'])
def get_jquery_viewer(file):
    """
    获取配置参数列表
    """
    mdict = {
        'css': 'text/css',
        'js': 'application/javascript;'
    }
    _tmparr = file.split('.')
    mime = mdict.get(_tmparr[len(_tmparr) - 1])
    if mime:
        img_path = __file__.replace('web_app.py', '') + file
        with open(img_path, 'rb') as f:
            image = f.read()
        return Response(image, mimetype=mime)
    if '.map' in file:
        return {'code': 404, 'msg': file}
    if 'favicon.ico' in file:
        return ''
    return render_template(file)


@app.route(base_uri + '/img/<img>', methods=['GET'])
def get_image(img):
    img_path = __file__.replace('web_app.py', '')+'img/' + img
    mdict = {
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif'
    }
    mime = mdict[(img_path.split('.')[1])]
    if not os.path.exists(img_path):
        # Res 是我自己定义的返回类，raw方法将数据组成字典返回
        return {'code': 404}
    with open(img_path, 'rb') as f:
        image = f.read()
    return Response(image, mimetype=mime)


@app.route('/<font>', methods=['GET'])
def get_font(font):
    img_path = __file__.replace('web_app.py', '')+'font/' + font
    mdict = {
        'woff2': 'application/font-woff2',
    }
    mime = mdict[(img_path.split('.')[1])]
    if not os.path.exists(img_path):
        # Res 是我自己定义的返回类，raw方法将数据组成字典返回
        return {'code': 404}
    with open(img_path, 'rb') as f:
        image = f.read()
    return Response(image, mimetype=mime)


@app.route(base_uri + '/delete', methods=['GET'])
def delete():
    """
    删除商品（单个或多个）
    """
    goods_ids = request.args.get('goods_ids')
    db_util.delete(goods_ids)
    return {'code': 1, 'msg': 'success'}


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/detail', methods=['GET'])
def detail():
    goods_code = request.args.get('goods_code')
    return render_template('detail.html')


@app.route('/get_base_info', methods=['GET'])
def get_base_info():
    """
    获取基本信息
    """
    goods_code = request.args.get('goods_code')
    info = db_util.select_base_info(goods_code)
    return {'code': '1', 'data': info}


@app.route('/list_codes', methods=['GET'])
def list_codes():
    page_no = request.args.get('page_no')
    du_price = request.args.get('du_price')
    stx_price = request.args.get('stx_price')
    price_diff = request.args.get('price_diff')
    price_diff_rate = request.args.get('price_diff_rate')
    stx_location = request.args.get('stx_location')
    spider_date_du = request.args.get('spider_date_du')
    spider_date_stx = request.args.get('spider_date_stx')
    # 除数
    price_diff_rate_divider = request.args.get('price_diff_rate_divider')
    search_cate = request.args.get('search_cate')
    if search_cate == 'null':
        search_cate = None
    rows, total = db_util.select_goods_skus(page_no=page_no, du_price_col=du_price, price_diff_rate=price_diff_rate,
                                            stx_price_col=stx_price, price_diff=price_diff,
                                            price_diff_rate_divider=price_diff_rate_divider, search_cate=search_cate,
                                            spider_date_du=spider_date_du, spider_date_stx=spider_date_stx)
    return {'code': 1, 'msg': 'success', 'data': rows, 'total_count': total}


@app.route('/del_all', methods=['GET'])
def del_all():
    """
    一键清除所有货号
    :return:
    """
    db_util.delete_all()
    return {'code': 1, 'msg': 'success'}

@app.route('/post_goods_codes', methods=['POST'])
def post_goods_codes():
    """
    提交货号
    """
    valid_count = import_goods_codes(request.data)
    return {'code': 1, 'msg': 'success', 'data': valid_count}


def import_goods_codes(data):
    """
    导入货号
    """
    body = json.loads(data)
    codes = body.get('codes')
    category = body.get('category')
    records = []
    for code in codes:
        records.append({'goods_code': code, 'create_time': time_util.get_now_str(), 'category': category})
    db_util.save_records(records, 't_goods_code')
    db_util.set_del_flag(codes, category=category)
    logger.info('成功导入 %s 个货号', len(records))
    return len(records)


@app.route('/get_sku_price_list', methods=['GET'])
def get_sku_price_list():
    code = request.args.get('code')
    rows = db_util.select_sku_price_list(code)
    return {'code': 1, 'msg': 'success', 'data': rows}


@app.route('/save_config', methods=['POST'])
def save_config():
    """
    保存参数配置
    """
    config_desc = {
        'du_tech_money': 'du技术服务费率（%）',
        'du_transfer_money': 'du转账服务费率（%）',
        'du_check_money': 'du查验费（元）',
        'du_discern_money': 'du鉴别（元）',
        'du_pkg_money': 'du包装服务费（元）',
        'stx_trade_money_rate': 'stx【卖出】交易费率（%）',
        'stx_transfer_money_rate': 'stx【卖出】转账手续费率（%）',
        'stx_buy_fee_rate': 'stx【购买】手续费率（%）',
        'stx_postage_money': 'stx 【购买】运费（元）',
        'outer_postage_money_usa': '运出国-美国运费（元）',
        'back_postage_money_usa': '运回国-美国运费（元）',
        'exchange_rate_rmb_dollar': '当前人民币-美元汇率 （%）'
    }
    records = []
    for k, v in request.form.items():
        if not v:
            continue
        records.append({
            'name': k,
            'value': v,
            'descr': config_desc.get(k)
        })
    if records:
        db_util.save_records(records, 't_config')
        logger.info('成功保存 %s 条配置', len(records))
    # return render_template('config.html')
    return {'code': 1, 'msg': '操作成功'}


@app.route('/load_config', methods=['GET'])
def load_config():
    """
    加载配置
    """
    config = db_util.select_config_dict()
    return {'code': 1, 'data': config}


@app.route('/get_sale_report', methods=['get'])
def get_sale_report():
    """
    获取走势图
    """
    code = request.args.get('code')
    sku_name = request.args.get('size')
    day_num = request.args.get('day_num')
    day_before = time_util.get_time_before(days=int(day_num)-1)[0: 10]
    date_list = time_util.get_day_list(day_before)
    rows_du = db_util.select_sale_report_du(code, sku_name, day_before)
    report_du = _parse_sale_report_dict(rows_du)
    rows_stx = db_util.select_sale_report_stx(code, sku_name, day_before)
    report_stx = _parse_sale_report_dict(rows_stx)
    du_sales = []
    du_prices = []
    stx_sales = []
    stx_prices = []
    for date in date_list:
        du_sales.append(report_du.get(date, {'sale_num': 0}).get('sale_num'))
        du_prices.append(report_du.get(date, {'avg_price': 0}).get('avg_price'))
        stx_sales.append(report_stx.get(date, {'sale_num': 0}).get('sale_num'))
        stx_prices.append(report_stx.get(date, {'avg_price': 0}).get('avg_price'))
    ret_data = {'code': 1, 'data': {'date_list': date_list, 'du_sales': du_sales,
                                    'du_prices': du_prices, 'stx_sales': stx_sales, 'stx_prices': stx_prices}}
    return json.dumps(ret_data)


def _parse_sale_report_dict(rows):
    """
    解析每日销售报表数据
    """
    report = {}
    for row in rows:
        report[row[2]] = {
            'sale_num': row[3],
            'avg_price': round(float(row[4]), 2)
        }
    return report


@app.route('/calculator/search', methods=['get'])
def calculator_search():
    """
    计算器搜索功能
    """
    code = request.args.get('code')
    fee_rate_du = request.args.get('fee_rate_du')
    fee_rate_stx = request.args.get('fee_rate_stx')
    plat_types = request.args.get('plat_types')
    data = web_api.query_detail_by_code(code, fee_rate_du, fee_rate_stx, plat_types)
    return json.dumps(data)
    # return json.dumps({"code": 1, "data": {"base_info": {"code": "DA8571-200", "du": {"name": "Nike Air Force 1 '07 PRM \"Touch Of Gold\" \u7c89\u9ed1 \u91d1\u5c5e", "sell_date": "/", "price": 719.0, "sell_num": 2040, "sell_num_3days": "/", "sell_num_7days": "/"}, "stx": {"name": "Nike Air Force 1 Low '07 PRM Particle Beige", "sell_date": "2021-07-26", "price": 130, "sell_num": 69, "sell_num_3days": "/", "sell_num_7days": "/"}}, "detail": {"du": [{"code": "DA8571-200", "sku_name": "38.5", "price_normal": 1499.0, "price_normal_get": 1331.09, "price_shan": '', "price_shan_get": '', "price_ji": '', "price_ji_get": '', "price_oversea": '', "price_want": '', "price_want_get": '', "spider_time": "2021-12-19 10:06:33"}, {"code": "DA8571-200", "sku_name": "39", "price_normal": 899.0, "price_normal_get": 785.09, "price_shan": '', "price_shan_get": '', "price_ji": '', "price_ji_get": '', "price_oversea": '', "price_want": '', "price_want_get": '', "spider_time": "2021-12-19 10:06:33"}, {"code": "DA8571-200", "sku_name": "40", "price_normal": 869.0, "price_normal_get": 757.79, "price_shan": 879.0, "price_shan_get": 766.89, "price_ji": '', "price_ji_get": '', "price_oversea": '', "price_want": '', "price_want_get": '', "spider_time": "2021-12-19 10:06:33"}, {"code": "DA8571-200", "sku_name": "40.5", "price_normal": 719.0, "price_normal_get": 621.29, "price_shan": 759.0, "price_shan_get": 657.69, "price_ji": '', "price_ji_get": '', "price_oversea": '', "price_want": '', "price_want_get": '', "spider_time": "2021-12-19 10:06:33"}, {"code": "DA8571-200", "sku_name": "41", "price_normal": 719.0, "price_normal_get": 621.29, "price_shan": 889.0, "price_shan_get": 775.99, "price_ji": '', "price_ji_get": '', "price_oversea": '', "price_want": '', "price_want_get": '', "spider_time": "2021-12-19 10:06:33"}, {"code": "DA8571-200", "sku_name": "42", "price_normal": 799.0, "price_normal_get": 694.09, "price_shan": 899.0, "price_shan_get": 785.09, "price_ji": '', "price_ji_get": '', "price_oversea": '', "price_want": '', "price_want_get": '', "spider_time": "2021-12-19 10:06:33"}, {"code": "DA8571-200", "sku_name": "42.5", "price_normal": 739.0, "price_normal_get": 639.49, "price_shan": 829.0, "price_shan_get": 721.39, "price_ji": 749.0, "price_ji_get": 648.59, "price_oversea": '', "price_want": '', "price_want_get": '', "spider_time": "2021-12-19 10:06:33"}, {"code": "DA8571-200", "sku_name": "44", "price_normal": 849.0, "price_normal_get": 739.59, "price_shan": 1099.0, "price_shan_get": 967.09, "price_ji": '', "price_ji_get": '', "price_oversea": 999.0, "price_want": '', "price_want_get": '', "spider_time": "2021-12-19 10:06:33"}, {"code": "DA8571-200", "sku_name": "44.5", "price_normal": 979.0, "price_normal_get": 857.89, "price_shan": '', "price_shan_get": '', "price_ji": '', "price_ji_get": '', "price_oversea": 799.0, "price_want": '', "price_want_get": '', "spider_time": "2021-12-19 10:06:33"}, {"code": "DA8571-200", "sku_name": "43", "price_normal": 769.0, "price_normal_get": 666.79, "price_shan": 829.0, "price_shan_get": 721.39, "price_ji": 809.0, "price_ji_get": 703.19, "price_oversea": '', "price_want": '', "price_want_get": '', "spider_time": "2021-12-19 10:06:33"}, {"code": "DA8571-200", "sku_name": "45", "price_normal": 889.0, "price_normal_get": 775.99, "price_shan": 909.0, "price_shan_get": 794.19, "price_ji": 929.0, "price_ji_get": 812.39, "price_oversea": '', "price_want": '', "price_want_get": '', "spider_time": "2021-12-19 10:06:33"}, {"code": "DA8571-200", "sku_name": "46", "price_normal": 919.0, "price_normal_get": 803.29, "price_shan": 999.0, "price_shan_get": 876.09, "price_ji": '', "price_ji_get": '', "price_oversea": '', "price_want": '', "price_want_get": '', "spider_time": "2021-12-19 10:06:33"}], "stx": [{"code": "DA8571-200", "price_buy": 450, "sku_name": "38.5", "price_sell": 109, "sell_get_price": 2577.6, "want_get_price": 624.35, "price_buy_get": 3228.48, "spider_time": "2021-12-19 10:06:38"}, {"code": "DA8571-200", "price_buy": 298, "sku_name": "40", "price_sell": 138, "sell_get_price": 1706.94, "want_get_price": 790.46, "price_buy_get": 2168.13, "spider_time": "2021-12-19 10:06:38"}, {"code": "DA8571-200", "price_buy": 163, "sku_name": "40.5", "price_sell": 37, "sell_get_price": 933.66, "want_get_price": 211.94, "price_buy_get": 1226.37, "spider_time": "2021-12-19 10:06:38"}, {"code": "DA8571-200", "price_buy": 152, "sku_name": "41", "price_sell": 78, "sell_get_price": 870.66, "want_get_price": 446.78, "price_buy_get": 1149.63, "spider_time": "2021-12-19 10:06:38"}, {"code": "DA8571-200", "price_buy": 136, "sku_name": "42", "price_sell": 116, "sell_get_price": 779.01, "want_get_price": 664.45, "price_buy_get": 1038.02, "spider_time": "2021-12-19 10:06:38"}, {"code": "DA8571-200", "price_buy": 132, "sku_name": "42.5", "price_sell": 111, "sell_get_price": 756.1, "want_get_price": 635.81, "price_buy_get": 1010.11, "spider_time": "2021-12-19 10:06:38"}, {"code": "DA8571-200", "price_buy": 124, "sku_name": "43", "price_sell": 83, "sell_get_price": 710.27, "want_get_price": 475.42, "price_buy_get": 954.3, "spider_time": "2021-12-19 10:06:38"}, {"code": "DA8571-200", "price_buy": 127, "sku_name": "44", "price_sell": 85, "sell_get_price": 727.46, "want_get_price": 486.88, "price_buy_get": 975.23, "spider_time": "2021-12-19 10:06:38"}, {"code": "DA8571-200", "price_buy": 160, "sku_name": "44.5", "price_sell": 37, "sell_get_price": 916.48, "want_get_price": 211.94, "price_buy_get": 1205.44, "spider_time": "2021-12-19 10:06:38"}, {"code": "DA8571-200", "price_buy": 156, "sku_name": "45", "price_sell": '', "sell_get_price": 893.57, "want_get_price": '', "price_buy_get": 1177.54, "spider_time": "2021-12-19 10:06:38"}, {"code": "DA8571-200", "price_buy": 135, "sku_name": "45.5", "price_sell": '', "sell_get_price": 773.28, "want_get_price": '', "price_buy_get": 1031.04, "spider_time": "2021-12-19 10:06:38"}, {"code": "DA8571-200", "price_buy": 199, "sku_name": "46", "price_sell": 101, "sell_get_price": 1139.87, "want_get_price": 578.53, "price_buy_get": 1477.5, "spider_time": "2021-12-19 10:06:38"}, {"code": "DA8571-200", "price_buy": 179, "sku_name": "47.5", "price_sell": '', "sell_get_price": 1025.31, "want_get_price": '', "price_buy_get": 1337.98, "spider_time": "2021-12-19 10:06:38"}]}}});
    # return json.dumps({"code": 1, "data": {"base_info": {"code": "314192-117", "du": {"name": "\u3010\u5723\u8bde\u9001\u793c\u63a8\u8350\u3011Nike Air Force 1 '07 Low (GS) \u7a7a\u519b\u4e00\u53f7 \u4f4e\u5e2e\u4f11\u95f2\u677f\u978b \u767d\u8272", "sell_date": "/", "price": 639.0, "sell_num": 775976, "sell_num_3days": "/", "sell_num_7days": "/"}, "stx": {"name": "Nike Air Force 1 Low White 2014 (GS)", "sell_date": "2014-01-01", "price": 75, "sell_num": 3657, "sell_num_3days": "/", "sell_num_7days": "/"}}, "detail": {"du": [{"code": "314192-117", "sku_name": "35.5", "price_normal": 749.0, "price_normal_get": 694.28, "price_shan": 749.0, "price_shan_get": 694.28, "price_ji": '', "price_ji_get": '', "price_oversea": '', "price_want": 649.0, "price_want_get": 597.18, "spider_time": "2021-12-18 21:06:25"}, {"code": "314192-117", "sku_name": "36", "price_normal": 639.0, "price_normal_get": 587.47, "price_shan": 639.0, "price_shan_get": 587.47, "price_ji": 649.0, "price_ji_get": 597.18, "price_oversea": 'null', "price_want": 539.0, "price_want_get": 490.37, "spider_time": "2021-12-18 21:06:25"}, {"code": "314192-117", "sku_name": "36.5", "price_normal": 709.0, "price_normal_get": 655.44, "price_shan": 729.0, "price_shan_get": 674.86, "price_ji": 719.0, "price_ji_get": 665.15, "price_oversea": 'null', "price_want": 619.0, "price_want_get": 568.05, "spider_time": "2021-12-18 21:06:25"}, {"code": "314192-117", "sku_name": "37.5", "price_normal": 679.0, "price_normal_get": 626.31, "price_shan": 689.0, "price_shan_get": 636.02, "price_ji": 'null', "price_ji_get": 'null', "price_oversea": '', "price_want": 549.0, "price_want_get": 500.08, "spider_time": "2021-12-18 21:06:25"}, {"code": "314192-117", "sku_name": "38", "price_normal": 739.0, "price_normal_get": 684.57, "price_shan": 809.0, "price_shan_get": 752.54, "price_ji": 739.0, "price_ji_get": 684.57, "price_oversea": 'null', "price_want": 589.0, "price_want_get": 538.92, "spider_time": "2021-12-18 21:06:25"}, {"code": "314192-117", "sku_name": "38.5", "price_normal": 639.0, "price_normal_get": 587.47, "price_shan": 669.0, "price_shan_get": 616.6, "price_ji": 659.0, "price_ji_get": 606.89, "price_oversea": 'null', "price_want": 509.0, "price_want_get": 461.24, "spider_time": "2021-12-18 21:06:25"}, {"code": "314192-117", "sku_name": "39", "price_normal": 669.0, "price_normal_get": 616.6, "price_shan": 699.0, "price_shan_get": 645.73, "price_ji": 'null', "price_ji_get": 'null', "price_oversea": 'null', "price_want": 539.0, "price_want_get": 490.37, "spider_time": "2021-12-18 21:06:25"}, {"code": "314192-117", "sku_name": "40", "price_normal": 659.0, "price_normal_get": 606.89, "price_shan": 679.0, "price_shan_get": 626.31, "price_ji": 669.0, "price_ji_get": 616.6, "price_oversea": 'null', "price_want": 549.0, "price_want_get": 500.08, "spider_time": "2021-12-18 21:06:25"}]}}})


@app.route('/save_monitor', methods=['POST'])
def save_monitor():
    """
    保存监控提醒
    """
    params = json.loads(request.data)
    codes = params.get('codes')
    if codes:
        # params['codes'] = ','.join(codes.split('\n'))
        params['codes'] = ','.join(codes.split('\r\n'))
    if not params.get('id'):
        # 新增
        params['create_time'] = time_util.get_now_str()
        db_util.save_one(params, 't_monitor')
    else:
        db_util.update_one(params, 't_monitor', {'id': params.get('id')})
    return json.dumps({'code': 1, 'msg': 'success'})


@app.route('/list_monitor', methods=['get'])
def list_monitor():
    """
    查询监控提醒
    """
    rows = db_util.select_monitors()
    for r in rows:
        codes = r.get('codes')
        size_list = db_util.select_sku_size_by_code(codes)
        r['size_list'] = size_list
    return json.dumps({'code': 1, 'msg': 'success', 'data': rows})


@app.route('/monitor_detail', methods=['get'])
def monitor_detail():
    _id = request.args.get('id')
    row = db_util.select_monitor(_id)[0]
    return json.dumps({'code': 1, 'msg': 'success', 'data': row})


@app.route('/delete_monitor', methods=['get'])
def delete_monitor():
    """
    删除监控详情
    """
    _id = request.args.get('id')
    db_util.delete_monitor(_id)
    return json.dumps({'code': 1, 'msg': 'success'})


@app.route('/select_task_status', methods=['get'])
def select_task_status():
    """
    查询任务状态
    """
    search_cate = request.args.get('search_cate')
    if search_cate == 'null':
        search_cate = None
    total, invalid_count, finish_count, remain_count = db_util.select_task_status(search_cate=search_cate)
    return {'code': 1, 'data': {'total': total, 'invalid_count': invalid_count,
                                'finish_count': finish_count, 'remain_count': remain_count}}


@app.route('/select_task_code_detail', methods=['get'])
def select_task_code_detail():
    task_type = request.args.get('task_type')
    rows = db_util.select_task_codes(task_type)
    return {'code': 1, 'data': rows}


@app.route('/spider_real_time', methods=['post'])
def spider_real_time():
    """
    实时采集接口
    """
    codes = request.form.get('codes')
    # rows = db_util.select_task_codes(task_type)
    task_du = db_util.select_goods_by_codes(codes, 'du_goods_id')
    resp_du = DuSpider.spider_sku_price_by_codes(task_du)
    if resp_du.get('code') != 1:
        return {'code': 1, 'msg': resp_du.get('msg')}
    task_stx = db_util.select_goods_by_codes(codes, 'sx_short_desc')
    resp_stx = StockxSpider.spider_sku_price_by_codes(task_stx)
    msgs = [resp_du.get('msg'), resp_stx.get('msg')]
    return {'code': 1, 'msg': ';\n'.join(msgs)}


@app.route('/fetch_exchange_rate', methods=['get'])
def fetch_exchange_rate():
    """
    实时抓取汇率（美元-人民币）
    """
    url = 'https://www.baidu.com/s?ie=utf-8&mod=1&isbd=1&isid=f43d2c2c00037695&ie=utf-8&f=8&rsv_bp=1&rsv_idx=1&tn=02003390_82_hao_pg&wd=%E6%B1%87%E7%8E%87&fenlei=256&oq=%25E6%25B1%2587%25E7%258E%2587&rsv_pq=f43d2c2c00037695&rsv_t=52ebtegMNLccnqXUa%2F7RDCp8iXTzUeOPvTcoYxxUighfBL8Quu48%2FS%2FPjrE9WJTj3C53aUHpzfYb&rqlang=cn&rsv_enter=0&rsv_dl=tb&rsv_btype=t&rsv_sug=1&bs=%E6%B1%87%E7%8E%87&rsv_sid=&_ss=1&clist=57ed55f9aa9e19e3&hsug=&f4s=1&csor=2&_cr1=32346'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Host': 'www.baidu.com',
        'cookie': 'BD_UPN=12314753; H_WISE_SIDS=107313_110085_127969_176398_178384_178619_179456_180276_181482_181588_182531_183327_184009_184320_184560_184737_184793_184826_184891_184892_185268_185519_186159_186318_186597_186716_186841_186843_187088_187292_187346_187356_187362_187433_187449_187530_187543_187669_187820_187828_187928_187960_188031_188182_188426_188731_188747_188755_188841_188872_188935_188992_189056_189104_189141_189272_189326_189347_189391_189417_189431_189679_189703_189713_189731_189737_189755_190113_190169_190520_190621_190682_190724_8000058_8000107_8000119_8000136_8000145_8000162_8000171_8000179_8000184_8000185; MSA_WH=375_812; __yjs_duid=1_c25efb7fbbf2108ebbe81ac76a40e2b51640054882296; BDORZ=FFFB88E999055A3F8A630C64834BD6D0; PSTM=1640672463; BIDUPSID=AA5EEAD7D598EEB5DA5846C5D11A46FA; BAIDUID=2CE17112CD9F57665A3CCB103F5A3D8E:FG=1; BDRCVFR[qlDlC709LmT]=tGHYk5goppDpA7Euvqduvt8mv3; BD_HOME=1; H_PS_PSSID=; delPer=0; BD_CK_SAM=1; BDRCVFR[pb8TAXzI710]=mk3SLVN4HKm; PSINO=7; H_PS_645EC=52ebtegMNLccnqXUa%2F7RDCp8iXTzUeOPvTcoYxxUighfBL8Quu48%2FS%2FPjrE9WJTj3C53aUHpzfYb; BA_HECTOR=0lakak8g0l8g8g8gmp1gsqb7n0r; BDSVRTM=179; COOKIE_SESSION=124_0_9_9_10_10_0_1_9_9_2_0_63896_0_0_0_1640831295_0_1640836341%7C9%231722025_48_1640569356%7C9; WWW_ST=1640836354718',
        'Referer': url
    }
    r = requests.get(url, headers=headers)
    rate = re.findall('1美元=(.*?)人民币', r.text)
    return {'code': 1, 'rate': rate}


@app.route('/save_category', methods=['get'])
def save_category():
    cate_name = request.args.get('name')
    db_util.save_one({'name': cate_name}, 't_category')
    return {'code': 1, 'msg': 'success'}


@app.route('/list_category', methods=['get'])
def list_category():
    rows = db_util.select_category()
    return {'code': 1, 'msg': 'success', 'data': rows}


@app.route('/get_codes_by_cate', methods=['get'])
def get_codes_by_cate():
    name = request.args.get('name')
    rows = db_util.select_codes_by_cate(name)
    return {'code': 1, 'data': rows}


@app.route('/delete_cate_and_codes', methods=['get'])
def delete_cate_and_codes():
    name = request.args.get('name')
    rows = db_util.del_by_cate(name)
    return {'code': 1}


def run_web(port):
    app.run(port=port, host='0.0.0.0', threaded=True, debug=True, )


if __name__ == '__main__':
    # start_all_task()
    stx_cookie = stockx_api.cookie
    wx_app_login_token = dewu_api_v2.wx_app_login_token
    x_auth_token = dewu_api_v2.x_auth_token
    sk = dewu_api_v2.sk
    if stx_cookie and wx_app_login_token and x_auth_token and sk:
        run_web(18866)
    else:
        logger.error('没有获取到账号cookie信息，请在配置文件配置后重启程序！！！')
        time.sleep(30)

