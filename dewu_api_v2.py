# -*- coding: utf-8 -*-
"""
@Author: admin
@Function: xxx
"""
import base64
import re
import hashlib
import json
import rsa_util
import urllib
import time
from aes_util import prpcrypt
import requests
import execjs
from log_conf import logger
# import sys, io
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gb18030')

# 主号
# wx_app_login_token = 'eea69e1e|df8e3d736ebcc0590ffc3cf2ff92d0b4|d93da726|6cfbc96b'
# x_auth_token = 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjE3MDYwMDE1MzYsInVzZXJOYW1lIjoi54ix54Ot6Ze56buR6buE6ISa6La-YzE4IiwiZXhwIjoxNjcwMzgwNTUyLCJpYXQiOjE2Mzg4NDQ1NTJ9.Lowy617OxNdLp3QPxOuW_nhuLp_tR9C0FfGX0QdiLe2rC42AR8KdeEG_1HIiXWaLcYwuojKDdKMbZkCJpwgTXV-A6r-bamBUnMXW9XuxBS6DO2J_2VtAWY59eBjiDhML6jlD-zwV3h6r3ltj0f9CI5E_TwdhbS8fJrjNiQlCSTme1kR4Bs2qeUPwkKz9SGBw_seIhcCr1sC8bySrBd-yyPDGAolDfgVgQ3DmTu-O_d0rm2HU-bB4ROZQQDVH6sAlZouUtRmb4IfFSoLRQoa7snA2wPSl0LIiCPWPEcXtvsMUviMkesmBMTh50Y2vql9FpAyG39OtonOR6bOdywKnwA'
# sk = 'VidKtBOzvWU%2BPPk6b0Hp%2BGRl3%2Bg4xj6E70%2BT49%2FacY6YbM0W7ZjqaxLPeCscKzLz'

# f = open('D:\workspace2\python\my_spider_2022\dewu_stockx\conf.ini', 'r')
# f = open('D:\my_workspace\my_spider_2022\dewu_stockx\conf.ini', 'r')
f = open('conf.ini', 'r')
conf = f.read()
wx_app_login_token = re.findall("wx_app_login_token = '(.*)'", conf)[0]
x_auth_token = re.findall("x_auth_token = '(.*)'", conf)[0]
sk = re.findall("sk = '(.*)'", conf)[0]


def hex2char(data):
    """
    根据返回数据获得aes加密数据
    """
    b_data = bytes.fromhex(data)
    return base64.b64encode(b_data).decode()


def char_to_hex(txt):
    new_txt = base64.b64decode(txt)
    return ''.join(['%02X' % b for b in new_txt])


def get_aes_obj(origin_key):
    aes_key = origin_key[10: 26]
    iv = origin_key[20: 36]
    # print(f'origin_key:{origin_key}, aes_key:{aes_key}, iv:{iv}')
    return prpcrypt(aes_key, iv)


def js_concat(a, b):
    # ctx = execjs.compile('''
    #         function concat(a, b){
    #         var s = a + "​" + b;
    #         return s;
    #     }
    # ''')
    ctx = execjs.compile(open(r'D:\workspace2\python\my_spider\dewu_stockx\myconcat.js', 'r', encoding='unicode').read())
    return ctx.call('concat', a, b)


def param_encrypt(src_params, is_search=False, is_web=False):
    """
    请求参数加密，json格式字符串，
    如商品详情：{"sign": "263625efd36998fbd148d87d4c0139ac", "spuId": "1031816", "productSourceName": "", "propertyValueId": "",
         "sourceName": "shareDetail"}
    """
    origin_key = prpcrypt.generate_aes_key(code_len=48)
    # src_params = json.dumps({"sign":"263625efd36998fbd148d87d4c0139ac","spuId":"11819","productSourceName":"","propertyValueId":"","sourceName":"shareDetail"})
    # 提交参数加密算法及拼接方式
    # encryt_params = {"data": RSA.encryt(aeskey) + char_to_hex(aes.encrypt(src_params))}
    if is_search:
        # 新公钥
        public_key = '''-----BEGIN PUBLIC KEY-----
        MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANSuWgzWxJ1a26/6c3nrCQP68acn9tyQr6rD02HmLKhnge9yg65nNvYdtcWAKWPu27ibIL3bvqdmJUUWKD3VG10CAwEAAQ==
        -----END PUBLIC KEY-----'''
        encrypt_aes_key = rsa_util.rsa_encrypt(origin_key, pub_key=public_key)
    else:
        if is_web:
            public_key_web = '''-----BEGIN PUBLIC KEY-----
                    MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANMGZPlLobHYWoZyMvHD0a6emIjEmtf5Z6Q++VIBRulxsUfYvcczjB0fMVvAnd1douKmOX4G690q9NZ6Q7z/TV8CAwEAAQ==
                    -----END PUBLIC KEY-----'''
            encrypt_aes_key = rsa_util.rsa_encrypt(origin_key, pub_key=public_key_web)
        else:
            encrypt_aes_key = rsa_util.rsa_encrypt(origin_key)
    aes_obj = get_aes_obj(origin_key)
    encrypt_params = aes_obj.encrypt(src_params)
    concat_str = ''
    if is_search or is_web:
        concat_str = u'\u200B'
    # 商品搜索接口(GET请求)有 \u200b 不可见字符
    post_data = {"data": encrypt_aes_key + concat_str + encrypt_params}
    return {"post_data": post_data, "x": origin_key}


def resp_decrypt(encrypt_data, origin_key):
    """
    响应参数解密
    origin_key 为加密的时候返回的x参数
    """
    encrypt_data = hex2char(encrypt_data)
    decrypt_data = get_aes_obj(origin_key).decrypt(encrypt_data)
    return decrypt_data


def goods_detail(spu_id, _proxy=None, stop_on_error=False):
    """
    获取商品详情
    """
    # param_dict
    param_dict = {"spuId": spu_id, "productSourceName": "", "propertyValueId": "", "sourceName": "shareDetail"}
    param_dict['sign'] = sign(param_dict, salt='19bc545a393a25177083d4a748807cc0')
    src_params = json.dumps(param_dict)
    encrypt_info = param_encrypt(src_params, is_search=True)
    post_data = encrypt_info.get('post_data')
    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'AppId': 'h5',
        'appVersion': '4.4.0',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        # 'Content-Length': '387',
        'Content-Type': 'application/json',
        'Host': 'app.dewu.com',
        'Origin': 'https://m.dewu.com',
        'platform': 'h5',
        'sks': '1,hdw1',
        'SK': sk,
        'Wxapp-Login-Token': wx_app_login_token,
        'X-Auth-Token': x_auth_token,
        'Pragma': 'no-cache',
        'Referer': 'https://m.dewu.com/',
        'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat'
    }

    headers = {
        'Host': 'app.dewu.com',
        'Connection': 'keep-alive',
        'AppId': 'wxapp',
        'SK': sk,
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat',
        'Wxapp-Login-Token': wx_app_login_token,
        'X-Auth-Token': x_auth_token,
        'appVersion': '4.4.0',
        'content-type': 'application/json',
        'platform': 'h5',
        'sks': '1,xdw1',
        'Referer': 'https://servicewechat.com/wx3c12cdd0ae8b1a7b/271/page-frame.html',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    # api = 'https://app.dewu.com/api/v1/h5/index/fire/flow/product/detail'
    api = 'https://app.dewu.com/api/v1/h5/index/fire/flow/product/detailV3'
    # r = requests.post(api, data=json.dumps(post_data), headers=headers, proxies=proxy_util_v2.get_my_proxy_direct(1))
    r = requests.post(api, data=json.dumps(post_data), headers=headers, proxies=_proxy)
    encrypt_data = r.text
    if '请校验验证码' in encrypt_data and not stop_on_error:
        logger.warning('详情页，请输入验证码...')
        time.sleep(30)
        return goods_detail(spu_id)
    if '请求已拒绝' in encrypt_data and not stop_on_error:
        logger.warning('详情页，拒绝请求,请切换ip...')
        time.sleep(300)
        return goods_detail(spu_id, _proxy=_proxy)
    if r.status_code != 200:
        return r.text
    return _decrypt_data(encrypt_data, encrypt_info)


def goods_detail_web(spu_id, _proxy=None):
    """
    获取商品详情
    """
    # param_dict
    param_dict = {"spuId": spu_id, "productSourceName": "", "propertyValueId": "", "sourceName": "shareDetail"}
    param_dict['sign'] = sign(param_dict)
    src_params = json.dumps(param_dict)
    encrypt_info = param_encrypt(src_params, is_web=True)
    post_data = encrypt_info.get('post_data')
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh,zh-CN;q=0.9',
        'AppId': 'h5',
        'appVersion': '4.4.0',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Length': '356',
        'Content-Type': 'application/json',
        'Cookie': 'sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2217dfae18084ac8-0f586db3f184f9-5437971-304500-17dfae180851167%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%2217dfae18084ac8-0f586db3f184f9-5437971-304500-17dfae180851167%22%7D',
        'Host': 'app.dewu.com',
        'Origin': 'https://m.dewu.com',
        'platform': 'h5',
        'Pragma': 'no-cache',
        'Referer': 'https://m.dewu.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        # 'sessionid': '4f890bf7-0c4a-44cd-8135-ea50a659381f',
        # 'shumeiId': 'BVP/YvI6nEh9STs8QgcBz/PEWSYYKvAWwVJqu9BoWM5bMFeiFgvrViCispDNpYcOGo2TZ+05gXKZ/+BIoSNw3lQ==',
        # 'SK': 'WhKe6XbTvFIHz9%2FvydipJfqfNyTAM7XdZBlqcH92Pqv9CgqEhORWATw1jULmJbpb',
        'sessionid': 'd1424698-44ec-4980-a69e-7affcc317edc',
        'shumeiId': 'DeyJhcHBJZCI6ImRlZmF1bHQiLCJvcmdhbml6YXRpb24iOiJyVXNzRGptVlB3aXF4OFFwalhVayIsImVwIjoiVHFRa1pqNDRUYWNWK1c4ZUJPSGM2OFFLa3RqNEl1bXUrQUVsaXNlSFFld2w2OHJ1bmJ5TVVOUFdHdEplV2ZORm5mZElGWHY5d2pMSDl6bmZWa0ZSYnVaR05UaWsxVWZDSkx3SlFFRURFV3FicHBBZU1GZ1VMVys5VUlQTVZPTWozSklmQTNNbFpMdjQxNlNOYlRHdnUzeU9pSG12bVNsZ3JVcTZiTGNuVFY0PSIsImRhdGEiOiIyM2QyM2E4MWQ1NDIxMjRmMGM4NWNkMGIzZTlmMjIwNGRmODBhZmMzOWFhYjM1ZTU2ZmI2N2M2NzE5Mjk3ODhkNmQ0YzFmMzUwZjY5MTBjNjMxZjI0MTUwOTAwY2I2M2FjNzBmYjIzYjc2NWRkMmRhN2YxMjY0NmFlZGJhMDU2ZWJjMWJlZTg5NDYyMGFkMTlhMTE4YzY0ZWJjYmQwZTZmMDU2NDg3ZWVjNWM1ZDM5ODM1ZTY5YjMwMmMxOGI0NTljNDUyN2Q1YmMyY2QwNDA1NTRiNTYxZWZkMDk2NTMwZDk4ODhiZTQ3MjI3YzQyYTIzNzY0ZDhiNzk5YWI4NmRjNDFhM2EwNTUwN2M0NDI5OGJlN2I1YmE4ZWM4NTk1NWI1MjUzYTdjODRkNGU4Y2U2ZmRjY2Q5YTI4NjkzMjYyNDI3NjFjMGFkZjNhNWY5ZWY2OGNiMTEyNjZlYjA3Yzk4MDIwNTVjY2MwMjQ1NzY1YjM5ZmQ1MGYzNzM3NThjZjZmM2ZlMjhjYmY0MTgyZjgzMGExYTUyZWU4YmEzNDZmMzhmYzFkNTE5OWI0ZDVhM2M3ZTQ2NzNmZTdkNTkxZjAyYTE0NzVkMDIyYzI0MDMyY2U0NzMyMWFmMGZlNmQyY2FjYTM1NGMwY2QyODczYzUyYTczZmZlYjhhM2I0OTczMjNjMWNkNDZmZDM4YTM1NWY5MWI2N2ExYTZhN2VlM2M2YTNmNDFhMDg0MjcyNzMwZWRlMmFlNGVkMThhYzRjMTVhZmVkMzQzZWUyMzQwYTkyN2QzZmJiMzRhY2I3ZmI5ZTczZDgyNTQ3MTI5ZjIzNTYyNGRjNDBmYmMyMWY5MTk1YzY1MTNkY2RjYTQ4MWJhMDBiM2NhM2VjMGMxMWNkZTYyMzIxN2M2YjBlYTE1NzI2NmNlNjlhOGE4YWNhODdmMWI4ZmM2YjhmMjlkZTRlYWEwMmVhMzA4NjAxMTBmYmJhNGNkYTA1YTU1NjE0ZjRmYzliYmJlNTJhMWIyMjFkMTdjOTM2NWZlOGMxZDNhZjcwZDY3YTkxN2I5YWRmMDc1NzFmYjAxMTBmYjI2MTM5MjA4NWI3YTdkZjgzOWIwZGNmNzgyMzA1ZWUxNWE4NWY2MjQ3NzI0NDU5YmZjYjQyOTJkMzc3ZmJkNDZjYjJhMDkxYTYwZDI0NTY5YzU2MmEzNGI1YzM3MzA3ZWZiYTVmY2NhNjhlYWM1MGQ0NDc2YjYzN2Q3MDhkN2YxYzc3MDg0ZjczYjJiM2FiMTM2MGRjY2VmY2ZkZTgzYzllZTBmNDAzNTkxNDJjNzhjNjBiOTAwZTI4Mjc4MmE0YTQxMjU0ZWYwZDUzMDNmMGIwZTU4NjFhNGY4YTZiYWE3NDRkNDNlYzA4ZDdiZTNmZGIzZjIyMzllYTM4MDI1YTM3MmNlM2U2Y2VhZmNjNGZkNzJiMWNhMTFlYTYwODhlYjdkY2RjMjMxMzc1OGQ4NzQ3NzcwNDI3YTcyZjBmOTdiMzU4MzU5M2E1ZDQyNDdlNTJlYTY3MDg1NjY5N2NmYzYyN2Y0YzE5MGU5ZGNhYTdhZDg3YzhiZjFhZWYyMTgzNjYyMGI5NDY5ZWJkM2Y0ZmJkZGE2NmNhYTdmNGYzMjVlYThiMzJjNmFkMDUxNTJmNzVhYjgwZTdmMWYyZjY5YzdiOWExYTY4YjhkZDBhZGQyY2YxYTEyMTUzYjc5MTk3ODQ5NmJmMjY5ZjRiYjM2NTkyMjVlNTI1NjA5YWU2YTg1NzM0NjU0N2M5ZmUxYjk4ZWFiMDcwZTA0NWFmNjNjYWRlY2JhODFiNTFhNmE1ZGQ2Mzk5ODhiMDg2MjI1OWZkZjliNjVhNjM3OGQzNjNiZjBjZTE2ZmUyMTE5NWZkM2ZmOTNlYzM1NGU4YzE3OTc4MjgzZDYzZTJiZmJkY2IyZjQwNDc5ZmJhNzMwNGE3NmM5OGQyNzQ0NTdlMGNjZTkxNzM2ZmJhZTVmY2MyYmFkNjZlNTIzNjI3MmQ5YmJmYjI1YWY1NjY1ZTk4NDc5NmNhMTViN2Q3MTY1ZDJhY2JiNGNjZTVhMzE5YjMxNDYxN2M1ZTgyYzUzODhiMjY0M2NmOTc3MjA2ODdlZjBiZDJjZTU1NmZmM2VhODQzOWQ3ZmZiZmYzYmI0YTc2YTM3OTRiYTNkZTBkOGU5MzRkZmFkNjc1MjE1Y2FkODBjZjQ1MmMxMTdiNzdhMjNkMjEzMWFmYmFjM2Y0ZGY1ZDY2ZDY5ZWQwOTAyMGVkMTI4NjhhMDk5MDk2OWMyMTFiODE5NmQ5OTE3NWE3ODZmZWI0ZTdkMzM1MTIzNWRmOWNmNjE5MGZkN2M1MjVhYzU0NDExZTAwNTk3NThmYzkwZDc4NGFiNmU5NTRlMjRkMDAwYThjZTEzM2U5OGQ1NGNmYWZjNzg4ODg2NTFiYjYyZmVjYmVkNGZmODBhMDNkOTVjMDUxYWQ3MzBlNzczNjRjMjZkZmU2NWEyYjljM2Y3ODNlYTFhM2QxMmYyNzQ4YjRlNWRjMjI1YWMyZjA3N2U3ZTMyNjY3NjljYmM4MGFmOTU4YmMwZmViOTc1MDUzYjg0ODM5ZTQxZjk1Y2ZiN2NkNDVkNWIyOGE4NmIwMDkzNTg1ZTNmMjdjOThhNTYxMTZiZmY3NzY5NWJiMGIyYTU1M2VkZDkzMzIwYjFkZGVmMTQwOTNkMWIzODk4NWNjMDAxMjQ0MGQ2NGY1OGU2ZTA4MzMwMjZiZWE5ZWZiNjNmMGM5ZDdkNTFiODMxYWVlY2ZkN2FlNTU4OGVhZWJjZDYwM2ZhYjYxZmIxZTgwYjIiLCJvcyI6IndlYiIsImVuY29kZSI6NSwiY29tcHJlc3MiOjJ9',
        'SK': '%2BeGWuX3laFrNo6Lbr7MiHosFbKDwsTsxUrJwQ%2FT%2FSICDkssgSjbiMjHENF99%2FgM%2F',
        'sks': '1,hdw3',
        # 'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363'
    }
    api = 'https://app.dewu.com/api/v1/h5/index/fire/flow/product/detailV3'
    r = requests.post(api, data=json.dumps(post_data), headers=headers, proxies=_proxy)
    encrypt_data = r.text
    if '请校验验证码' in encrypt_data:
        logger.warning('详情页，请输入验证码...')
        time.sleep(30)
        return goods_detail_web(spu_id)
    if '请求已拒绝' in encrypt_data:
        logger.warning('详情页，拒绝请求,请切换ip...')
        time.sleep(300)
        return goods_detail_web(spu_id, _proxy=_proxy)
    return _decrypt_data(encrypt_data, encrypt_info)


def search(keywords, _proxy=None, stop_on_error=False):
    """
    搜索商品
    :param keywords:
    :param _proxy:
    :param stop_on_error: 出错是否返回
    :return:
    """
    api = 'http://app.dewu.com/api/v1/h5/search/fire/search/list'
    body = {"title": keywords, "page": 0, "sortType": 0, "sortMode": 1, "limit": 20, "showHot": 1, "isAggr": 1}
    _sign = sign(body, salt='19bc545a393a25177083d4a748807cc0')
    src_params = f"sign={_sign}&title={keywords}&page=0&sortType=0&sortMode=1&limit=20&showHot=1&isAggr=1"
    encrypt_info = param_encrypt(src_params, is_search=True)
    post_data = encrypt_info.get('post_data')
    api = api + '?data=' + urllib.parse.quote(post_data.get('data'), safe='')
    headers = {
        'Host': 'app.dewu.com',
        'Connection': 'keep-alive',
        'AppId': 'wxapp',
        'SK': sk,
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat',
        'Wxapp-Login-Token': wx_app_login_token,
        'X-Auth-Token': x_auth_token,
        'appVersion': '4.4.0',
        'content-type': 'application/x-www-form-urlencoded',
        'platform': 'h5',
        'sks': '1,xdw1',
        'Referer': 'https://servicewechat.com/wx3c12cdd0ae8b1a7b/271/page-frame.html',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    # proxy = {
    #     'http': 'http://127.0.0.1:8888',
    #     'https': 'http://127.0.0.1:8888'
    # }
    r = requests.get(api, headers=headers, proxies=_proxy)
    encrypt_data = r.text
    if '请校验验证码' in encrypt_data and not stop_on_error:
        logger.warning('商品搜索，请输入验证码...')
        time.sleep(30)
        return search(keywords)
    if '请求已拒绝' in encrypt_data and not stop_on_error:
        logger.warning('商品搜索，拒绝请求,请切换ip...')
        time.sleep(300)
        return search(keywords, _proxy=_proxy)
    if r.status_code != 200:
        return r.text
    return _decrypt_data(encrypt_data, encrypt_info)


def _decrypt_data(encrypt_data, encrypt_info):
    origin_key = encrypt_info.get('x')
    decrypt_data = resp_decrypt(encrypt_data, origin_key)
    # print(decrypt_data)
    return decrypt_data


def search_goods_old(code, proxy=None):
    """
    根据编号搜索商品
    """
    sign_params = {'title': code, 'page': 0, 'sortType': 0, 'sortMode': 1, 'limit': 20, 'showHot': 1, 'isAggr': 1}
    api = f'https://app.dewu.com/api/v1/h5/search/fire/search/list?title={code}&page=0&sortType=0&sortMode=1&limit=20&showHot=1&isAggr=1'
    sig = sign(sign_params)
    api = api + '&sign=' + sig
    headers = {
        'Host': 'app.dewu.com',
        'Connection': 'keep-alive',
        'AppId': 'wxapp',
        'SK': 'VidKtBOzvWU%2BPPk6b0Hp%2BGRl3%2Bg4xj6E70%2BT49%2FacY6YbM0W7ZjqaxLPeCscKzLz',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat',
        'appVersion': '4.4.0',
        # 'content-type': 'application/json',
        'platform': 'h5',
        'sks': '1,xdw1',
        'Referer': 'https://servicewechat.com/wx3c12cdd0ae8b1a7b/271/page-frame.html',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    r = requests.get(api, headers=headers, proxies=proxy)
    print(r.text)
    return r.text


def sku_price_list(goods_id, proxy=None, stop_on_error=False):
    """
    获取商品下不同码数的价格
    """
    api = 'https://app.dewu.com/api/v1/h5/inventory/price/h5/queryBuyNowInfo'
    sig = sign({"spuId": goods_id}, salt='19bc545a393a25177083d4a748807cc0')
    params = {"sign": sig, "spuId": goods_id}
    src_params = json.dumps(params)
    encrypt_info = param_encrypt(src_params, is_search=True)
    post_data = encrypt_info.get('post_data')
    headers = {
        'Host': 'app.dewu.com',
        'Connection': 'keep-alive',
        'Content-Length': '230',
        'AppId': 'wxapp',
        'SK': sk,
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat',
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'Wxapp-Login-Token': wx_app_login_token,
        'X-Auth-Token': x_auth_token,
        'appVersion': '4.4.0',
        'content-type': 'application/json',
        'platform': 'h5',
        'sks': '1,xdw1',
        'Referer': 'https://servicewechat.com/wx3c12cdd0ae8b1a7b/271/page-frame.html',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    r = requests.post(api, data=json.dumps(post_data), headers=headers, proxies=proxy)
    # if '"code":200' not in r.text:
    #     print(f'{goods_id} sku_price_list 请求失败，{r.text}')
    if '请校验验证码' in r.text and not stop_on_error:
        logger.warning('价格列表，请输入验证码...')
        time.sleep(30)
        return sku_price_list(goods_id)
    if r.status_code != 200 and not stop_on_error:
        logger.warning('请求异常!!! %s', r.text)
        time.sleep(30)
        return sku_price_list(goods_id)
    if r.status_code != 200:
        return r.text
    return _decrypt_data(r.text, encrypt_info)


def sku_price_list_web(goods_id, proxy=None, stop_on_error=False):
    """
    获取商品下不同码数的价格
    """
    api = 'https://app.dewu.com/api/v1/h5/inventory/price/h5/queryBuyNowInfo'
    sig = sign({"spuId": goods_id})
    params = {"sign": sig, "spuId": goods_id}
    src_params = json.dumps(params)
    encrypt_info = param_encrypt(src_params, is_web=True)
    post_data = encrypt_info.get('post_data')
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh,zh-CN;q=0.9',
        'AppId': 'h5',
        'appVersion': '4.4.0',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Length': '228',
        'Content-Type': 'application/json',
        'Cookie': 'sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2217dfae18084ac8-0f586db3f184f9-5437971-304500-17dfae180851167%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%2217dfae18084ac8-0f586db3f184f9-5437971-304500-17dfae180851167%22%7D',
        'Host': 'app.dewu.com',
        'Origin': 'https://m.dewu.com',
        'platform': 'h5',
        'Pragma': 'no-cache',
        'Referer': 'https://m.dewu.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'sessionid': '4f890bf7-0c4a-44cd-8135-ea50a659381f',
        'shumeiId': 'BKFgpXPemyXfwSMhck4wtjL6E9qjUb3Gm8bg9D7ImKl8ExaQQ3RDMWGWvNrryiAAPDg3nfAWF4PU+iJrBEzDNFQ==',
        'SK': 'WhKe6XbTvFIHz9%2FvydipJfqfNyTAM7XdZBlqcH92Pqv9CgqEhORWATw1jULmJbpb',
        'sks': '1,hdw3',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
    }
    r = requests.post(api, data=json.dumps(post_data), headers=headers, proxies=proxy)
    # if '"code":200' not in r.text:
    #     print(f'{goods_id} sku_price_list 请求失败，{r.text}')
    if '请校验验证码' in r.text and not stop_on_error:
        logger.warning('价格列表，请输入验证码...')
        time.sleep(30)
        return sku_price_list_web(goods_id)
    if r.status_code != 200 and not stop_on_error:
        logger.warning('请求异常!!! %s', r.text)
        time.sleep(30)
        return sku_price_list_web(goods_id)
    if r.status_code != 200:
        return r.text
    return _decrypt_data(r.text, encrypt_info)


def sku_price_info(detail, price_list):
    """
    获取sku对应的价格
    """
    sku_size = sku_2_size(detail)
    data = json.loads(price_list).get('data')
    sku_info_list = data.get('skuInfoList')
    for info in sku_info_list:
        # sku_price[info.get('skuId')] = info.get('minPrice')
        info['sku_name'] = sku_size.get(info.get('skuId'))
    return sku_info_list


def sku_2_size(goods_detail):
    """
    获取每个尺码对应的sku
    """
    data = json.loads(goods_detail).get('data')
    # 尺码
    if not data:
        return {}
    sale_props = data.get('saleProperties')
    size_props = sale_props.get('list')
    # 尺码对应的属性id
    size_prop_id = {}
    for prop in size_props:
        prop_name = prop.get('name')
        if '尺码' != prop_name:
            continue
        size_prop_id[prop.get('propertyValueId')] = prop.get('value')
    # 获取尺码对应的skuid
    skus = data.get('skus')
    sku_size = {}
    for sku in skus:
        sku_id = sku.get('skuId')
        properties = sku.get('properties')
        for prop in properties:
            size = size_prop_id.get(prop.get('propertyValueId'))
            if not size:
                continue
            sku_size[sku_id] = size
    return sku_size


def view_buyer(spu_id):
    """
    获取求购价(旧版小程序接口)
    """
    api = 'https://app.dewu.com/api/v1/h5/newbidding/buyer/view'
    body = {"spuId": spu_id}
    body['sign'] = sign(body, salt='19bc545a393a25177083d4a748807cc0')
    headers = {
        'Host': 'app.dewu.com',
        'Connection': 'keep-alive',
        'AppId': 'wxapp',
        'SK': 'VidKtBOzvWU%2BPPk6b0Hp%2BGRl3%2Bg4xj6E70%2BT49%2FacY6YbM0W7ZjqaxLPeCscKzLz',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat',
        # 'Wxapp-Login-Token': 'eea69e1e|9ad6079a3a449378a4f2f2c9edb4e6de|6b4a31f1|6cfbc96b',
        # 'X-Auth-Token': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoibnVsbCIsInVzZXJJZCI6MTcwNjAwMTUzNiwidXNlck5hbWUiOiLniLHng63pl7npu5Hpu4TohJrotr5jMTgiLCJleHAiOjE2NjY5MzkzOTksImlhdCI6MTYzNTQwMzM5OSwiaXNzIjoibnVsbCIsInN1YiI6Im51bGwifQ.nK1xkK5LW0Re7w5Pbu2xSIq8JZNGbOO1MTsiElA4d8VwOusGLpTZbTBv-mzs5c4FTTBObQt3raCBmgBeDK5EZTfXRldPvodO8uoopaWtA9mGQuAQPMzDpeBhiOTnoV1GPyTzSdVLd4OMzk2DplRVcwoEPJUYMXvzD7P_vIgEgFYrxJAIPOqx-9nqBN3KvMOcsWm9w0mfU67wwmcOrrEjKKNAmP0WwtncZvVHlDHsFlbeUuTHJzygxq90Q3RCgiM-NWMZDp9FEz92i1UAWri-9BRCodqzjJqjad12Tur1e27VtTIRQ2SBJlk360Xl7y01kIrh6FsjXjv0BDGZR83EWA',
        'appVersion': '4.4.0',
        'content-type': 'application/json',
        'platform': 'h5',
        'sks': '1,xdw1',
        'Referer': 'https://servicewechat.com/wx3c12cdd0ae8b1a7b/271/page-frame.html',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    r = requests.post(api, data=json.dumps(body), headers=headers)
    # print(r.text)
    return r.text


def sign(jsonObj:dict,trim=False, salt='048a9c4943398714b356a696503d2d36')->str:
    """
    参数签名
    """
    keys = jsonObj.keys()
    sorted_obj = {i:jsonObj[i] for i in sorted(keys)}
    _str = ''.join([f'{k}{"" if not v and isinstance(v,list) else str(v).replace(" ","")}' for k,v in sorted_obj.items()]) + salt
    _str=_str.replace("'",'"')
    if trim:
        _str=re.sub('[\[\]]',_str,'')
    md5 = hashlib.md5()
    md5.update(bytes(_str,'utf-8'))
    return md5.hexdigest()


def last_sold_list(goods_id, _proxy=None):
    """
    获取最近购买记录
    """
    api = 'https://app.dewu.com/api/v1/h5/commodity/fire/last-sold-list'
    headers = {
        'Host': 'app.dewu.com',
        'Connection': 'keep-alive',
        'Content-Length': '230',
        'AppId': 'wxapp',
        'SK': sk,
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat',
        'Wxapp-Login-Token': wx_app_login_token,
        'X-Auth-Token': x_auth_token,
        'appVersion': '4.4.0',
        'content-type': 'application/json',
        'platform': 'h5',
        'sks': '1,xdw1',
        'Referer': 'https://servicewechat.com/wx3c12cdd0ae8b1a7b/271/page-frame.html',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    params = {"spuId": goods_id}
    sig = sign(params, salt='19bc545a393a25177083d4a748807cc0')
    # params = {"sign": sig, "spuId": goods_id}
    params["sign"] = sig
    src_params = json.dumps(params)
    encrypt_info = param_encrypt(src_params, is_search=True)
    post_data = encrypt_info.get('post_data')
    r = requests.post(api, data=json.dumps(post_data), headers=headers, proxies=_proxy)
    encrypt_data = r.text
    if '请校验验证码' in encrypt_data:
        logger.warning('订单记录，请输入验证码...')
        time.sleep(30)
        return last_sold_list(goods_id)
    if '请求已拒绝' in encrypt_data:
        logger.warning('订单记录，拒绝请求,请切换ip...')
        time.sleep(300)
        return last_sold_list(goods_id, _proxy=_proxy)
    return _decrypt_data(encrypt_data, encrypt_info)


def get_goods_by_code(num, stop_on_error=False):
    """
    根据货号搜索商品信息
    :param num:
    :param stop_on_error:
    :return:
    """
    s = search(num, stop_on_error=stop_on_error)
    if stop_on_error and ('请校验验证码' in s or '请求已拒绝' in s):
        return s
    s = json.loads(s)
    status = s.get('status')
    if status != 200:
        logger.error('未获取到搜索结果：%s', s)
        time.sleep(3)
        return False
    result_list = s.get('data').get('productList')
    matched_product = None
    for r in result_list:
        article_num = r.get('articleNumber')
        if article_num == num:
            matched_product = r
            break
    if not matched_product:
        logger.warning('%s 未匹配到商品id', num)
        time.sleep(3)
        return False
    return matched_product


if __name__ == '__main__':
    # hex_data = '2858DF2183590A214F15DDDA42A5DFC70B8A90C85E870F2BB330CD821D8D93C708AD2AE7509A5696B47A8B31101087BB4D3D2ADF93375EA52FED51732784924CC71235A039E02E9E4F7055717760B22DB819E1C4A3DD7F15FD05E212EA43F7E5C4EC8921772889AE4FB12459864DF5E7CE8202B49546E508AEDAE8663066D26D91541C829EA531F2F9B981BB806BBC74'
    # aes_encode_str = hex2char(hex_data)
    # print(aes_encode_str)
    # print(generate_aes_key(48))
    # hex_data = 'DD3E367D0383533028FCEAA083DDF4143D85F26380EAD74BA45AB664B7B7C4D95568D7587E6567CC13AE6C7937855E5B1110039C592A29F5AC11E748DB0636A518478092D0712FA158FA0E2D26838F96407206FEA63C3C99DC807FBF149441183D5E6C9FA1ADA5FBC24A10B3DDA7E061322693E75F29B9AEF5C7150D1E92D22B3F7E5268E2F6E3318232B31B08E133EE'
    # hex_data = '68C7BB12994015FBA29BF0AC44D40FE6DDE44484FE067AB94727D0FCF1D474FBB2AD964DF1C920C0ADC0CEA1DAB6DC283F3E0D5CC2CC7FEB41FC0E10D1F437A571889625F7C0649675F38059EDF7613AED9528C18D472B77F53939D282078E8B7AF0E452B1A2F953E4010A24BB9B299DCACFABAAC9241AB76EE9BD5EE9ED7AFB361A7C22FC3F548A8E661F74C8728D95'
    # print(hex2char(hex_data))
    # s = 'aMe7EplAFfuim/CsRNQP5t3kRIT+Bnq5RyfQ/PHUdPuyrZZN8ckgwK3AzqHattwoPz4NXMLMf+tB/A4Q0fQ3pXGIliX3wGSWdfOAWe33YTrtlSjBjUcrd/U5OdKCB46LevDkUrGi+VPkAQoku5spncrPq6rJJBq3bum9Xuntevs2Gnwi/D9Uio5mH3TIco2V'
    # print(char_to_hex(s))
    import time
    goods_id = '1075922'
    goods_id = '10903'
    # detail = goods_detail(goods_id)
    # print(detail)
    # print(search('845104-102'))
    # print(view_buyer('80082'))
    # proxy = {
    #     'http': 'http://majora:arojam2021@139.155.225.214:30002',
    #     'https': 'http://majora:arojam2021@139.155.225.214:30002'
    # }
    # price_list = sku_price_list(goods_id, proxy=None)
    # sku_price = sku_price_info(detail, price_list)
    # print(json.dumps(sku_price, ensure_ascii=False))
    # a = last_sold_list(goods_id)
    # print(a)
    for gid in ['1260771','1952996','48076','1717935','75545','1919951','1493107','1705095','1574864','2130149','1953903','28653','28025','1237506','1190436','1483491','1023561','1273668','1292449','1188283','1416513','1048095','1065924','1067697','1321805','1054209','1424010','1426708','1065719','1229007','1430129','1440115','1335428','1271618','1267547','1501758','1161777','1449692','1582351','1032378','1596544','1349039','1343493','1279893','1280791','1278231','1237605','1280824','1279913','1399201','1067722','1196427','1476337','1015745','1451434','1275809','1280772','1362093','1362140','1283518']:
        # s = goods_detail(gid, stop_on_error=True)
        s = goods_detail_web(gid)
        print(s)
    # s = sku_price_list_web('2305')
    # print(s)
    #     if '请校验验证码' in s or '已拒绝' in s:
    #         print(s)
    #         break
    #     print('成功！')




