# -*- coding:utf-8 -*-
'''
Created on 2017年2月23日

@author: huangjiaxin
'''

import requests
import time
from bs4 import BeautifulSoup
from pybloom import BloomFilter, ScalableBloomFilter
import re
import redis
import logging
import threading
import pymongo
import MySQLdb
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def get_users():
    connect = MySQLdb.connect(host="localhost",user="qzone_spider",passwd="qzone_spider",db="db_tencent_wb",charset="utf8")
    cur = connect.cursor()
    cur.execute("select * from t_tencent_wb_wid")
    cur.scroll(0)
    p = cur.fetchone()
    users = []
    try:
        while p:
            users.append(str(p[2]))
            p = cur.fetchone()
    finally:
        cur.close()
        connect.close()
    return users


def popuserid():
    logging.info('get user_id')
    ids = []
    r = redis.Redis(host='192.168.8.25', port=6379, password='npq8pprjxnppn477xssn', db=0)
    while r.llen('tencent_wb_content_wid') > 0:
        if len(ids) >= 1000:
            return ids
        else:
            ids.append(r.rpop('tencent_wb_content_wid'))
    return ids

def getpage(user_id):
    url = "http://t.qq.com/" + str(user_id)
    r = requests.get(url)
    return r.text


def getinformation(page_code):
    information_dict = {}
    soup = BeautifulSoup(page_code,'html.parser')
    try:
        private_information = soup.find(name="div", attrs={"id":"LUI_wide"})
        user_name = private_information.find(name="h3").a
        information_dict["user_name"] = str(user_name.string)
        user_level = private_information.find(name="h3").find(name="a", attrs={"class":"ico_level"}).em
        information_dict["level"] = str(user_level.string)

        detail_information = private_information.find(name="div", attrs={"class":"m_profile_info"})
        city = detail_information.find(name="p", attrs={"class":"desc"}).find(name="a", attrs={"boss":"btnApolloCity"})
        if city:
            information_dict["city"] = str(city.string)
        else:
            information_dict["city"] = "None"
        work = detail_information.find(name="p", attrs={"class":"desc"}).find(name="a", attrs={"boss":"btnApolloWork"})
        if work:
            information_dict["user_work"] = str(work.string)
        else:
            information_dict["user_work"] = "None"

        summary = detail_information.find(name="p", attrs={"class":"summary"})
        information_dict["summary"] = str(summary)

        follow_information = private_information.find(name="div", attrs={"class":"m_profile"})
        messageCount = follow_information.find(name="a", attrs={"boss":"btnApolloMessageCount"}).span
        information_dict["messageCount"] = str(messageCount.string)
        fllowingCount = follow_information.find(name="a", attrs={"boss":"btnApolloFollowing"}).span
        information_dict["following"] = str(fllowingCount.string)
        followerCount = follow_information.find(name="a", attrs={"boss":"btnApolloFollower"}).span
        information_dict["follower"] = str(followerCount.string)

        item_num = 1
        talkList_dict = {}
        for item in soup.find(name="ul", attrs={"id":"talkList"}).find_all(name="li"):
            content_dict = {}
            msg_content = item.find(name="div", attrs={"class":"msgCnt"})
            if msg_content != None:
                msg_string = []
                for string in msg_content.stripped_strings:
                    msg_string.append(str(string))
            else:
                msg_string = "None"
            content_dict["msg_content"] = msg_string
    
            tran_content = item.find(name="div", attrs={"class":"replyBox"})
            if tran_content != None:
                tran_string = []
                for string in tran_content.stripped_strings:
                    tran_string.append(str(string))
            else:
                tran_string = "None"
            content_dict["tran_content"] = tran_string
            
            picturl_or_vedio = item.find(name="div", attrs={"class":"clear"})
            if picturl_or_vedio != None:
                picturl_or_vedio_string = []
                for string in picturl_or_vedio.stripped_strings:
                    picturl_or_vedio_string.append(str(string))
            else:
                picturl_or_vedio_string = "None"
            content_dict["picturl_or_vedio"] = picturl_or_vedio_string
    
            public_information = item.find(name="div", attrs={"class":"pubInfo"})
            platform = public_information.find(name="i", attrs={"class":"sico"})
            if platform:
                content_dict["platform"] = str(platform["title"])
            else:
                content_dict["platform"] = "None"
            date_time = public_information.find(name="a", attrs={"class":"time"})
            content_dict["date_time"] = str(date_time.string)
            talkList_dict[str(item_num)] = content_dict
            item_num += 1
        information_dict["talkList"] = talkList_dict
    except:
        return information_dict
    return information_dict
        

def dostore(information_list):
    logging.info('start doing store')
    client = pymongo.MongoClient("192.168.8.25",27017)
    database = client.db_tx_wb_content
    table_information = database.t_weibo_content
    for information_dict in information_list:
        table_information.insert(information_dict)
    client.close()
    logging.info('the storing is end')


def load(user_ids):
    information_list = []
    for user_id in user_ids:
        try:
            page_code = getpage(user_id)
            information_dict = getinformation(page_code)
        except Exception, e:
            logging.error(str(e))
            logging.error(user_id+"can't load")
            information_dict = {"information":"None"}
        information_dict["UserId"] = user_id
        information_list.append(information_dict)
    dostore(information_list)


class MyThread(threading.Thread):
    def run(self):
        user_ids = popuserid()
        while len(user_ids) > 0:
            try:
                load(user_ids)
            except Exception, e:
                logging.error(str(e))
            finally:
                user_ids = popuserid()


def main():
    logging.basicConfig(filename='logfile.log', datefmt='%Y/%m/%d %I:%M:%S %p', format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    threads = [MyThread() for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
            
if __name__ == '__main__':
    main()