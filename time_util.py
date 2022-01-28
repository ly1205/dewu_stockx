# -*- coding: utf-8 -*-
"""
@Time: 2021/7/21 17:48
@Function: xxx
"""
import time
import datetime
import pandas


def str_2_timestamp(str_time, fmt='%Y-%m-%d %H:%M:%S'):
    """
    字符串转时间戳
    :param str_time:
    :param fmt:
    :return:
    """
    time_array = time.strptime(str_time, fmt)
    time_stamp = int(time.mktime(time_array))
    return time_stamp


def get_now_time_stamp():
    return int(time.time())


def get_now_str():
    """
    获取当前时间
    :return: yyyy-MM-dd HH:mm:ss
    """
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_today_str():
    return get_now_str()[0:10]


def get_today_start_ts():
    return int(time.mktime(datetime.date.today().timetuple()))


def get_time_before(hours=0, minutes=0, days=0):
    """
    获取n天前的时间
    """
    today = datetime.datetime.now()
    ndays = today + datetime.timedelta(hours=-hours, minutes=-minutes, days=-days)
    return ndays.strftime('%Y-%m-%d %H:%M:%S')


def fmt_us_time(s):
    """
    格式化美国时间为中国时间
    """
    new_time = datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S+00:00')
    new_time = new_time + datetime.timedelta(hours=8)
    return new_time.strftime('%Y-%m-%d %H:%M:%S')


def str_2_date(date_str):
    return datetime.datetime.strptime(date_str, '%Y-%m-%d')


def get_day_list(start_date):
    """
    生成日期列表
    """
    return pandas.date_range(start_date, get_today_str()).strftime("%Y-%m-%d").to_list()
    # start = str_2_date(start_date)
    # curr = start
    # end = str_2_date(get_today_str())
    # day_list = []
    # while curr < end:
    #     yield curr
    #     curr += datetime.timedelta(days=1)
    #     day_list.append(curr)
    # return day_list


if __name__ == '__main__':
    # print(str_2_timestamp('2019-12-17 10:09', '%Y-%m-%d %H:%M'))
    # print(get_now_time_stamp())
    # print(get_today_start_ts())
    # print(get_today_str())
    # print(get_time_before(days=3)[0:10])
    # print(fmt_us_time('2021-12-06T23:00:59+00:00'))
    print(get_day_list('2021-12-01'))