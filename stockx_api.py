# -*- coding: utf-8 -*-
"""
@Author: admin
@Function: xxx
"""
import requests
import json
import time
from log_conf import logger
import stock_parse_util
import re

# cookie = '_pin_unauth=dWlkPVlqbG1ZVFprTVdVdFpqRTVPUzAwTURRd0xXSmxNR0V0T0RneVpHSTJabUl6Wm1Kaw; stockx_experiments_id=web-ec9e5adc-7265-4468-a331-27c5ee8a259b; _ga=GA1.2.235913526.1638265236; _pxvid=9230d01b-51c1-11ec-be6c-774656564755; ajs_group_id=ab_3ds_messaging_eu_web.false%2Cab_aia_pricing_visibility_web.novariant%2Cab_chk_germany_returns_cta_web.true%2Cab_chk_order_status_reskin_web.false%2Cab_chk_place_order_verbage_web.false%2Cab_chk_remove_affirm_bid_entry_web.true%2Cab_chk_remove_fees_bid_entry_web.true%2Cab_citcon_psp_web.true%2Cab_desktop_home_hero_section_web.control%2Cab_home_contentstack_modules_web.variant%2Cab_home_dynamic_content_targeting_web.control%2Cab_low_inventory_badge_pdp_web.variant_1%2Cab_pirate_recently_viewed_browse_web.false%2Cab_product_page_refactor_web.true%2Cab_recently_viewed_pdp_web.variant_1%2Cab_test_korean_language_web.true%2Cab_web_aa_1103.false; ajs_anonymous_id=46967c95-d7c6-4329-8e24-021ba0d25520; _gcl_au=1.1.852222348.1638265240; _ga=GA1.2.235913526.1638265236; _px_f394gi7Fvmc43dfg_user_id=OTUzOGQzMzEtNTFjMS0xMWVjLTlmNjEtMjkxNDdiNmNlNjJk; _fbp=fb.1.1638265241953.1796159836; stockx_dismiss_modal=true; stockx_dismiss_modal_expiration=2022-11-30T09%3A40%3A44.700Z; stockx_dismiss_modal_set=2021-11-30T09%3A40%3A44.700Z; QuantumMetricUserID=91cec06ad0eb88116f0202df8d1a59d8; rskxRunCookie=0; rCookie=n0sbt7yrfg7xptdc4v2ockwlgs3am; __pdst=8a26028f5dd045e68d778277b57cd246; _rdt_uuid=1638265245196.82fe7269-6ed8-449e-bd0b-00513bc36a1d; __ssid=d8d98b267c4001307223c0ae08ab86b; _scid=84a07146-f2f6-47dc-9ea6-493ce4f28381; tracker_device=2f2bbd7a-198c-4ad9-9906-c9d19ca7075b; stockx_seen_ask_new_info=true; _uetsid=9a14e080580811ec86c8bf11fa1888ac; _uetvid=8caba0d051c111ecbdd47f78dc26b7e6; IR_PI=1638265227756.kg9u4rqw1zl%7C1639041850920; stockx_homepage=sneakers; language_code=en; stockx_market_country=CN; pxcts=6f2aa8b0-5899-11ec-a609-61f7147b3961; stockx_product_visits=1; stockx_preferred_market_activity=sales; stockx_default_sneakers_size=All; hide_my_vices=false; stockx_session=%22c40d3825-40fd-475b-9c95-e5884a742ef1%22; __pxvid=6f78e3d7-5899-11ec-ad85-0242ac120002; _px3=3b3adc230f7bda3a64f677b93caf35b14bb899c1608481615839ded56797f52a:IGRPZGvX8PAIVEslKE3Ru+JaftAUS22iGOiZ9XdZl6lAng/QdWBYPml0IPk9/0UDCH9mHJQXGgbtQNjLwjAtZA==:1000:M4E969lp+Rx5LivgXfscZxta7iCmVLZ9dtjgQ2U66gANDV4XNsYs7kEJKUCMtKlmu/mhG2NW8TzZAdvfX4l4bxftyuZQiOviEXNnD9Y93DRTa8Iwe8YYrmULlTgSY3z3hRZILiwS7Mc9z2ZUIU7IVRBku9+kwBHK3NATcHlTFeU8vN72x57Dd/NIXDZtUoF4w5oH3qCr5ZdfprmjUA8LpQ==; riskified_recover_updated_verbiage=true; ops_banner_id=bltf0ff6f9ef26b6bdb; forterToken=e35812cebdd646e0804f47996d7c5df3_1639017658243__UDF43_13ck; lastRskxRun=1639017660491; _px_7125205957_cs=eyJpZCI6IjcxNDAxYjMwLTU4OTktMTFlYy04NGJhLTU5YmFmZGM5ZWRiYyIsInN0b3JhZ2UiOnt9LCJleHBpcmF0aW9uIjoxNjM5MDE5NTMxNDM1fQ==; _dd_s=rum=0&expire=1639018632394'
# cookie = '_px_f394gi7Fvmc43dfg_user_id=ZTJiYjI1ZjEtNjQ4MC0xMWVjLWI5ZmEtZTFhZDAzNjRiNTM0; pxcts=e2d5d9e0-6480-11ec-aa95-d5d8a924ad68; _pxvid=e2d557e5-6480-11ec-8b10-6c6b66626377; stockx_homepage=sneakers; stockx_experiments_id=web-f07eeae2-d5bd-4aad-a77e-9e96e681afac; stockx_market_country=CN; __pxvid=f197973a-6480-11ec-ad85-0242ac120002; stockx_default_sneakers_size=All; stockx_preferred_market_activity=sales; hide_my_vices=false; stockx_session=%22edfc9c54-cc53-4de5-b1df-ed24354c33f9%22; _ga=undefined; riskified_recover_updated_verbiage=true; ops_banner_id=bltf0ff6f9ef26b6bdb; __ssid=69535e29254554102351b80317abd8e; language_code=en; stockx_selected_locale=en; stockx_selected_region=CN; stockx_dismiss_modal=true; stockx_dismiss_modal_set=2021-12-24T06%3A15%3A57.319Z; stockx_dismiss_modal_expiration=2022-12-24T06%3A15%3A57.318Z; rskxRunCookie=0; rCookie=r0tzir6c47n2lvr3ebsjqkxk02wj6; stockx_product_visits=2; lastRskxRun=1640326560216; forterToken=9053ed1be0e94eaf93e09e98da45b434_1640326560172__UDF43_13ck; _px3=80b7c998d578f579cfbdf7dbe5dac952cbcd3c100da54d6d107e0d95d8caa045:7gls3ATeaKXSPYTS+PRs++ZN3wmBrIEnXr+TWPumoDVwAfLdVh++MsT7M22y4+sFgSAj0eR78r9/6JcbGNVgLg==:1000:mKiQ/ZsGUWAUhDpn0N0Xo3fywAlMUEfT2+CM59x+bQ2RceCiJXLal+JHXQc32oo7RSBEb1Vl8mq8OFg0zXjUAJuXFQRWOEBOegDlSyK+ubIvl1u0dta+EAI7My2GsZsJXx0d2VJS51W23u7wYXh0+WFFL+1lOe9JJQ+a2RI2cVIO6scj6Vk07qLjX+4Ti9sX+h+xD91EP1pK6RbOz/RLkA==; _px_7125205957_cs=eyJpZCI6IjM3MTY4MjIwLTY0ODYtMTFlYy1hNWFmLTM3MGUwMWVlYzI2YyIsInN0b3JhZ2UiOnt9LCJleHBpcmF0aW9uIjoxNjQwMzMwNjE1NDI3fQ==; _dd_s=rum=0&expire=1640329717873'
# cookie = '_px3=efb6e9a29902b9070a53bfab012b2a9083d11cb95676a0e05ab9aa3064bff9b6:CvO+UEktUF0UYTS6HiWkEsaNqXVbCAKhUndz45duRXFJIOIdQPKT0LvcT+kminp5VORy63ZIw++UOOfBo1l1lg==:1000:JDh+kKqcPggJV8+2suz19mBis1MC3j/bV5D1/9wtjXKMLaTx3PS/5ptuOQ/kiD1Wmisg7RZLIPQdGkZET+2F4Uo33xZFW7YjzG5JDB1XhnLhAsKo6FILwXqeVN76oFhTeyZ2/N+TLGbzbLYn77j2/RQU5gl3byVTP5tFsjv1TDqZAnnLOoJXgMoiM6jTL8mWHVa3Zz+A2hCqRpZtdft3Ow=='

# f = open('D:\workspace2\python\my_spider_2022\dewu_stockx\conf.ini', 'r')
# f = open('D:\my_workspace\my_spider_2022\dewu_stockx\conf.ini', 'r')
f = open('conf.ini', 'r')
conf = f.read()
cookie = re.findall("stx_cookie = '(.*)'", conf)[0]


def search(code='CT8012-005'):
    api = 'https://xw7sbct9v6-1.algolianet.com/1/indexes/products/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.11.0)%3B%20Browser'
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh,zh-CN;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Length': '48',
        'content-type': 'application/x-www-form-urlencoded',
        'Host': 'xw7sbct9v6-1.algolianet.com',
        'Origin': 'https://stockx.com',
        'Pragma': 'no-cache',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
        # 'x-algolia-api-key': 'MzA2NjZiZDBmY2RiNzhmMDgzM2E1ZjBiMDBmYWVmNWQzYmVmYWY4MWU1MGQ2MjBlNjdkMmQ3YzhmNWY2MDM4MHZhbGlkVW50aWw9MTYzODMyODM0MQ==',
        # 'x-algolia-application-id': 'XW7SBCT9V6'
        'x-algolia-api-key': 'MzA2NjZiZDBmY2RiNzhmMDgzM2E1ZjBiMDBmYWVmNWQzYmVmYWY4MWU1MGQ2MjBlNjdkMmQ3YzhmNWY2MDM4MHZhbGlkVW50aWw9MTYzODMyODM0MQ==',
        'x-algolia-application-id': 'XW7SBCT9V6'
    }
    params = {"query": code,"facets":"*","filters":""}
    r = requests.post(api, data=json.dumps(params), headers=headers)
    # print(r.text)
    return r.text


def search2(code, stop_on_error=False):
    api = f'https://stockx.com/api/browse?&_search={code}&dataType=product'
    headers = {
        'pragma': 'no-cache',
        'referer': 'https://stockx.com/search?s=555088-611',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'cookie': cookie,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }
    r = requests.get(api, headers=headers, timeout=15)
    s = r.text
    if s.startswith('<!DOCTYPE html>') or 'Access to this page has been denied' in s:
        logger.warning('拒绝访问！！！！')
        time.sleep(30)
        if not stop_on_error:
            return search2(code)
    return s


def goods_detail(short_description):
    url = f'https://stockx.com/{short_description}'
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        # 'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh,zh-CN;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'referer': 'https://stockx.com',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'cookie': cookie,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }
    # r = requests.get(url, headers=headers, proxies=proxy_util_v2.get_my_proxy_direct(1))
    r = requests.get(url, headers=headers)
    # print(r.text)
    return r.text


def goods_detail2(short_description):
    url = f'https://stockx.com/api/products/{short_description}?includes=market,360&currency=USD&country=CN'
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh,zh-CN;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'referer': 'https://stockx.com/search/sneakers?s=CT8012-005',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
    }
    r = requests.get(url, headers=headers)
    # print(r.text)
    return r.text


def sku_price_list():

    pass


def order_history(product_id):
    """
    商品购买记录
    """
    api = f'https://stockx.com/api/products/{product_id}/activity?limit=100&page=1&sort=createdAt&order=DESC&state=480&currency=USD&country=CN'
    headers = {
        'accept': 'application/json',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh,zh-CN;q=0.9',
        'app-platform': 'Iron',
        'app-version': '2021.12.01',
        'cache-control': 'no-cache',
        'referer': 'https://stockx.com/air-jordan-1-retro-high-og-a-ma-maniere',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'cookie': cookie,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }
    # r = requests.get(api, headers=headers, proxies=proxy_util_v2.get_my_proxy_direct(1))
    r = requests.get(api, headers=headers)
    return r.text


def get_goods_by_code(num, stop_on_error=False):
    """
    通过货号搜索商品
    :param num:
    :param stop_on_error:
    :return:
    """
    num = num.strip()
    s = search2(num, stop_on_error=stop_on_error)
    if stop_on_error and 'Access to this page has been denied' in s:
        return '拒绝访问，请切换ip!!'
    s = json.loads(s)
    products = s.get('Products')
    matched_product = None
    for p in products:
        style_id = p.get('styleId')
        # if style_id == num:
        if num in style_id.split('/'):
            matched_product = p
            break
    if not matched_product:
        logger.warning('货号 %s 未搜索到商品', num)
        return False
    return matched_product


if __name__ == '__main__':
    # print(search2('555088-611'))
    htm = goods_detail('nike-air-presto-multi-color-storm')
    # htm = goods_detail('nike-air-force-1-shadow-phantom-w')
    # print(htm)
    dt = stock_parse_util.parse_detail(htm)
    print(json.dumps(dt))
    price_map = stock_parse_util.parse_sell_price_map(htm)
    print(price_map)
    # size_map = stock_parse_util.parse_size_map(htm, 'eu')
    # print(size_map)
    # htm = goods_detail('air-jordan-1-mid-paint-drip-gs')
    # # 解析详情，获取购买价格信息
    # detail = stock_parse_util.parse_detail(htm)
    # product_info = detail.get('Product')
    # brand = product_info.get('brand')
    # offers = detail.get('Product').get('offers').get('offers')
    # records = []
    # # 尺码转换
    # size_map = stock_parse_util.parse_size_map(htm, 'eu', brand=brand, goods_name=product_info.get('name'))
    pass


