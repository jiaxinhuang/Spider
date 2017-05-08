# -*- coding:utf-8 -*-
'''
Created on 2017年2月28日

@author: huangjiaxin
'''
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from pybloom import BloomFilter
import logging
import threading
import multiprocessing
import time
import re
import redis
import sys
import pymongo
import MySQLdb
reload(sys)
sys.setdefaultencoding('utf8')


def signin(login_number):
    driver = webdriver.PhantomJS()
    url = "http://qzone.qq.com/"
    driver.get(url)
    driver.switch_to_frame('login_frame')
    driver.find_element_by_id('switcher_plogin').click()
    driver.find_element_by_id('u').clear()
    driver.find_element_by_id('u').send_keys(login_number["number"])
    driver.find_element_by_id('p').clear()
    driver.find_element_by_id('p').send_keys(login_number["password"])
    driver.find_element_by_id('login_button').click()
    time.sleep(10)
    return driver


def dojudge(page_code):
    soup = BeautifulSoup(page_code, 'html.parser')
    if soup.find(name='body', attrs={'class':'no_privilege'}):
        return False
    else:
        return True


def getcode(driver,QQ_number):
    url = "http://user.qzone.qq.com/" + str(QQ_number)+ "/mood"
    driver.get(url)
    element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID,"app_canvas_frame")))
    driver.switch_to_frame('app_canvas_frame')
    element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID,"msgList")))
    time.sleep(10)
    return driver.page_source,driver


def getinformation(page_code):
    soup = BeautifulSoup(page_code, 'html.parser')
    msgList = soup.find(name='ol', attrs={'id':'msgList'})
    pinglun_people_list = []
    temp_information_dict = {}
    num = 1
    for feed in msgList.find_all(name='li', attrs={'class':'feed'}):
        information_dict = {}
        contents = feed.find(name='pre', attrs={'class':'content'})
        if contents:
            content = []
            for content_line in contents.stripped_strings:
                content.append(content_line)
        else:
            content = 'None'   
        information_dict['content'] = content
    
        rt_content = feed.find(name='div', attrs={'class':'md rt_content'})
        if rt_content:
            rt_contents = []
            for rt_content_line in rt_content.stripped_strings:
                rt_contents.append(rt_content_line)
        else:
            rt_contents = 'None'
        information_dict['rt_contents'] = rt_contents
    
        info_send = feed.find(name='div', attrs={'class':'ft'}).find(name='div', attrs={'class':'info'})
        if info_send:
            date_and_platform = []
            for info_line in info_send.stripped_strings:
                date_and_platform.append(info_line)
        else:
            date_and_platform = 'None'
        information_dict['date_and_platform'] = date_and_platform
    
        op_reader = feed.find(name='div', attrs={'class':'ft'}).find(name='div', attrs={'class':'op'})
        if op_reader:
            op_of_reader = []
            for op_line in op_reader.stripped_strings:
                op_of_reader.append(op_line)
        else:
            op_of_reader = 'None'
        information_dict['op_of_reader'] = op_of_reader
    
        mood_comments = feed.find(name='div', attrs={'class':'mod_comment'})
        mood_comments_list = []
        for pinglun_line in mood_comments.find_all(name='li', attrs={'class':'comments_item bor3'}):
            if pinglun_line:
#         if pinglun_line.find(name='div', attrs={'class':'mod_comments_sub'}):
                per_mood_comments_list = []
                comments_content = pinglun_line.find(name='div', attrs={'class':'comments_content'})
                nickname = comments_content.find(name='a', attrs={'class':'nickname'})
                people_number = re.findall(r'\d+', str(nickname['href']))[0]
                pl_words = []
                pl_words.append(people_number)
                pinglun_people_list.append(people_number)
                for pl_word in comments_content.stripped_strings:
                    pl_words.append(pl_word)
                per_mood_comments_list.append(pl_words)
            
                mod_comments_sub = pinglun_line.find(name='div', attrs={'class':'mod_comments_sub'})
                if mod_comments_sub:
                    for comment_sub in mod_comments_sub.find_all(name='li', attrs={'class':'comments_item bor3'}):
                        hf_nickname = comment_sub.find(name='a', attrs={'class':'nickname'})
                        hf_people_number = re.findall(r'\d+', str(hf_nickname['href']))[0]
                        hl_comment = []
                        pinglun_people_list.append(hf_people_number)
                        hl_comment.append(hf_people_number)
                        for hl_word in comment_sub.stripped_strings:
                            hl_comment.append(hl_word)
                        per_mood_comments_list.append(hl_comment)
                mood_comments_list.append(per_mood_comments_list)
        information_dict['mood_comments_list'] =  mood_comments_list
        temp_information_dict[str(num)] = information_dict
        num += 1  
#     print temp_information_dict
#     print pinglun_people_list
    return temp_information_dict, pinglun_people_list


def dofilter(friends_list):
    temp_list = []
    temp_bf = BloomFilter(capacity=1000, error_rate=0.001)
    for item in friends_list:
        if (item in temp_bf) == False:
            temp_bf.add(item)
            temp_list.append(item)
    return temp_list


def popnumbers():
    numbers = []
    r = redis.Redis(host='localhost', port=6379, db=0)
    while r.llen('tencent_qzone_number_iteration') > 0:
        if len(numbers) >= 1000:
            return numbers
        else:
            numbers.append(r.rpop('tencent_qzone_number_iteration'))
    return numbers


def dostore(friends_dict, information_list, load_list):
    logging.info('start doing store')
    try:
        client = pymongo.MongoClient("localhost",27017)
        database = client.db_shuoshuo_content
        table_information = database.t_shuoshuo_content
        for information_item in information_list:
            table_information.insert(information_item)
        client.close()
    
        connect = MySQLdb.connect(host="localhost",user="qzone_spider",passwd="qzone_spider",db="db_qzone_spider",charset="utf8")
        cur = connect.cursor()
    
        r = redis.Redis(host='localhost', port=6379, db=0)
        for item in load_list:
            r.lpushx('tencent_qzone_canload_number', item)
        with open('bfone.txt', 'rb') as f:
            bf_one = BloomFilter.fromfile(f)
        for user in friends_dict.keys():
            if len(friends_dict[user]) > 0:
                bf_two = BloomFilter(capacity=1000, error_rate=0.01)
                for friend in friends_dict[user]:
                    if (friend in bf_one) == False:
                        r.lpushx('tencent_qzone_number', friend)
                        r.lpush('tencent_qzone_number_iteration', friend)
                        bf_one.add(friend)
                    if (friend in bf_two) == False:
                        bf_two.add(friend)
                        cur.execute("INSERT INTO t_qzone_friends (user_number, friend_number) values (%s, %s)" % (user, friend))
                        connect.commit()
    except Exception, e:
        logging.error(str(e))
    finally:
        cur.close()
        connect.commit()
        connect.close()
        with open('bfone.txt','wb') as f:
            bf_one.tofile(f)
    
    logging.info('store end')


def load(numbers):
    login_number = {'number':'', 'password':''}
    driver = signin(login_number)
    load_list = []
    information_list = []
    friends_dict = {}
    for number in numbers:
        try:
            page, driver = getcode(driver, number)
            if dojudge(page) == False:
                load_dict = {'number:':str(number), 'can_load':'0'}
                information_dict = {}
            else:
                load_list.append(str(number))
                load_dict = {'number:':str(number), 'can_load':'1'}
                information_dict, friend_list = getinformation(page)
                friends_dict[str(number)] = friend_list
            total_information_dict = dict(load_dict, **information_dict)
            information_list.append(total_information_dict)
        except Exception, e:
            logging.error(str(e))
    dostore(friends_dict, information_list, load_list)
    time.sleep(3)
    driver.quit()


class MyThread(threading.Thread):
    def run(self):
        numbers = popnumbers()
        while len(numbers) > 0:
            try:
                load(numbers)
            except Exception, e:
                logging.error(str(e))
            finally:
                numbers = popnumbers()

    
def main():
    logging.basicConfig(filename='logfile.log', datefmt='%Y/%m/%d %I:%M:%S %p', format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    threads = [MyThread() for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        

if __name__ == '__main__':
    main()