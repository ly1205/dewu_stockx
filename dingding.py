# -*- coding:utf-8 -*-
# @Author : hujz
# @File : dingding_sendmess.py
# @Function : 钉钉机器人发送消息，告警

import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests


def get_sign():
    """
    # 钉钉设置加签
    :return:
    """
    timestamp = str(round(time.time() * 1000))
    secret = 'SEC663267ebc64951e702050ba4add0cac3522c629988679a9d39ca0fe8fa2ec4c1'
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


# 发送消息
def sendinfo_ding(data, atMobiles: list = [], isAtAll=False):
    """
    :param data: 需要发送的消息
    :param atMobiles: @人的手机号码, []格式， 例如[ "156xxxx8827", "189xxxx8325"]
    :param isAtAll: 是否发送给所有人，默认False
    :return:
    """
    timestamp, sign = get_sign()
    access_token = "08239deb8a806b97ec1cdfc1843a55d22c05114d0826374aaae036a74fc0fbd7"
    url = f"https://oapi.dingtalk.com/robot/send?access_token={access_token}&timestamp={timestamp}&sign={sign}"
    program = {
        "msgtype": "text",
        "text": {"content": data},
        "at": {
            "atMobiles": atMobiles,
            "isAtAll": isAtAll
        }
    }
    headers = {'Content-Type': 'application/json'}
    requests.post(url, data=json.dumps(program), headers=headers)
    return True


if __name__ == '__main__':
    sendinfo_ding(data='过去30分钟，得物平台售出20双！！', isAtAll=True)
    pass
    # 发送所有人测试
    # sendinfo_ding(data='测试, 发送给所有人!', isAtAll=True)
    # 选择@人测试，需要填写相关人员手机号码，钉钉会有特殊@提醒
    # sendinfo_ding(data='测试多个用户选择, 发送给的消息!', atMobiles=[13001209571, 13243815477])

