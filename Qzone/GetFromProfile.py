# -*- coding:utf-8 -*-
'''
Created on 2016年12月27日

@author: huangjiaxin
'''

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from pybloom import BloomFilter
import logging
import time
import redis
import re
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
    time.sleep(3)
    return driver


def get_firstpage(driver, number):
    url = "http://user.qzone.qq.com/" + str(number) + "/profile"
    driver.get(url)
    time.sleep(3)
    return driver.page_source, driver


def dojudge(page_code):
    soup = BeautifulSoup(page_code, 'html.parser')
    if soup.find(name='body', attrs={'class':'no_privilege'}):
        return False
    else:
        return True


def getinformationpage(driver):
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID,"app_canvas_frame")))
    driver.switch_to_frame('app_canvas_frame')
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID,"frameFeedList")))
    driver.switch_to_frame('frameFeedList')
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID,"host_home_feeds")))
    return driver.page_source


def getimformation(page_code):  
    soup = BeautifulSoup(page_code,'html.parser')
    temp_imformation_dict = {}
    sign_num = 1
    friend_list = []
    for li in soup.find_all(name='li', attrs={'class':'f-single'}):
        li_imformation_dict = {}
#             print '发送时间:',str(li.span.string)
        li_imformation_dict["send_time"] = str(li.span.string)
        
        phone_type = li.find(name='a', attrs={'class':'phone-style'})
        if phone_type:
#                 print '发送平台：',str(li.find(name='a', attrs={'class':'phone-style'}).string)
            li_imformation_dict["send_platform"] = str(li.find(name='a', attrs={'class':'phone-style'}).string)
        else:
#                 print "发送平台：电脑"
            li_imformation_dict["send_platform"] = "电脑"
            
#             print '浏览数: ',re.findall(r'\((\d*)\)',str(li.find(name='a',attrs={'data-clicklog':'visitor'}).contents[1]))[0]
        if li.find(name='a',attrs={'data-clicklog':'visitor'}):
            li_imformation_dict["see_num"] = re.findall(r'\((\d*)\)',str(li.find(name='a',attrs={'data-clicklog':'visitor'}).contents[1]))[0]
        
        shuoshuo_or_comment = li.find(name='div',attrs={'class':'f-info'})
#             print str(shuoshuo_or_comment)
        if shuoshuo_or_comment:
            shuoshuo_or_comment_string = []
            for string in shuoshuo_or_comment.stripped_strings:
                shuoshuo_or_comment_string.append(str(string))
        else:
            shuoshuo_or_comment_string = "None"
        li_imformation_dict["shuoshuo_or_comment"] = shuoshuo_or_comment_string
        picture_or_url = li.find(name='div',attrs={'class':'f-ct'})
#             print str(picture_or_url)
        if picture_or_url:
            picture_or_url_string = []
            for string in picture_or_url.stripped_strings:
                picture_or_url_string.append(str(string))
        else:
            picture_or_url_string = "None"
        li_imformation_dict["picture_or_url"] = picture_or_url_string
        
        #分离评论以及评论人数，转发人数，点赞人数
        fenli_imformation = li.find(name='div', attrs={'class':'f-op-wrap'})
    
    #评论人数
        pinglun = fenli_imformation.find(name='a',attrs={'data-clicklog':'comment'}).contents[1]
        if len(pinglun) > 2:
#                 print '评论人数:',re.findall(r'\((\d*)\)',str(pinglun))[0]
            li_imformation_dict["comment_num"] = re.findall(r'\((\d*)\)',str(pinglun))[0]
        else:
#                 print '评论人数:',str(0)
            li_imformation_dict["comment_num"] = "0"    
    #点赞人数
        dianzan = fenli_imformation.find(name='a',attrs={'data-clicklog':'like'}).contents[1]
        if len(dianzan) > 1:
#                 print '点赞人数:',re.findall(r'\((\d*)\)',str(dianzan))[0]
            li_imformation_dict["prise_num"] = re.findall(r'\((\d*)\)',str(dianzan))[0]
        else:
#                 print '点赞人数:',str(0)
            li_imformation_dict["prise_num"] = "0"
    
    #点赞人列表，转发的点赞是没有显示的
        dianzan_list = fenli_imformation.find(name='div',attrs={'class':'f-like'})
        prise_list = []
        if dianzan_list != None:
            for user in dianzan_list.find_all(name='a',attrs={'class':'item'}):
#                     print "空间链接",re.findall(r'/(\d*)',str(user["href"]))[2]
                prise_list.append(re.findall(r'/(\d*)',str(user["href"]))[2])
        else:
            prise_list = []
#                 print "can not get the list because of transponding"
        friend_list += prise_list
        li_imformation_dict["parise_list"] = prise_list
    #评论人列表
        pinglun_dict = {}
        pinglun_people = []
        if len(pinglun) > 2:
#                 print "评论"
            a = 1
            for item_pinglun in fenli_imformation.find(name='div', attrs={'class':'comments-list'}).find_all(name='li', attrs={'data-type':'commentroot'}):
            #评论发起人
                item_list = []
                pinglun_start = item_pinglun.find(name='div',attrs={'class':'comments-content'})
                pinglun_people.append(re.findall(r'_(\d*)',str(pinglun_start.a['link']))[0])
#                     print '评论人(qq):',re.findall(r'_(\d*)',str(pinglun_start.a['link']))[0],'内容:',str(pinglun_start.contents[2]),'评论时间:',str(pinglun_start.span.string)
                item_list.append(re.findall(r'_(\d*)',str(pinglun_start.a['link']))[0]+'+'+str(pinglun_start.contents[2])+'+'+str(pinglun_start.span.string))
            #回复提取
                huifuS = item_pinglun.find(name='div',attrs={'class':'comments-list mod-comments-sub'})
                if  huifuS:
                    for huifu in huifuS.find_all('li'):
                        if len(huifu.find(name='div',attrs={'class':'comments-content'})) >= 5:
#                             print '回复人（qq）:',str(huifu['data-uin']),'回复内容:',str(huifu.find(name='div',attrs={'class':'comments-content'}).contents[4]),'回复时间:',str(huifu.find(name='div',attrs={'class':'comments-op'}).span.string)
                            item_list.append(str(huifu['data-uin'])+'+'+str(huifu.find(name='div',attrs={'class':'comments-content'}).contents[4])+'+'+str(huifu.find(name='div',attrs={'class':'comments-op'}).span.string))
                    pinglun_dict[str(a)] = item_list
                    a = a+1
#                 print "item_list:",item_list
#             print pinglun_people
        friend_list += pinglun_people
        li_imformation_dict["pinglun_people_list"] = pinglun_people
        li_imformation_dict["pinglun_list"] = pinglun_dict
        temp_imformation_dict[str(sign_num)] =li_imformation_dict
        sign_num += 1
    return temp_imformation_dict, friend_list


def load(number, driver, signnumber):
    first_page, driver = get_firstpage(driver, number)
    if dojudge(first_page):
        load_dict = {"QQ_num":str(number), "can_load":"1"}
        information_dict = {}
        friend_list = []
        try:
            information_page = getinformationpage(driver)
            information_dict, friend_list = getimformation(information_page)
        except Exception, e:
            logging.error(str(e))
            information_dict["information"] = "can't get"
            driver.quit()
            driver = signin(login_number)
        return load_dict, information_dict,friend_list, driver
    else:
        load_dict = {"QQ_num":str(number), "can_load":"0"}
        information_dict = {}
        friend_list = []
        return load_dict, information_dict,friend_list, driver


def get_numbers():
    connect = MySQLdb.connect(host="localhost",user="qzone_spider",passwd="qzone_spider",db="db_qzone_spider",charset="utf8")
    cur = connect.cursor()
    cur.execute("select * from t_base_qq")
    cur.scroll(0)
    p = cur.fetchone()
    numbers = []
    try:
        while p:
            numbers.append(str(p[1]))
            p = cur.fetchone()
    finally:
        cur.close()
        connect.close()
    return numbers


def dostore(friends_dict, information_list, load_list):
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
        if item['can_load'] == '1':
            r.lpushx('tencent_qzone_canload_number', item['QQ_num'])
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
    cur.close()
    connect.commit()
    connect.close()
    
    with open('bfone.txt','wb') as f:
        bf_one.tofile(f)
    

def getbfone():
    with open('bfone.txt', 'rb') as f:
        bf_one = BloomFilter.fromfile(f)
    return bf_one


def popnumbers():
    numbers = []
    r = redis.Redis(host='localhost', port=6379, db=0)
    while r.llen('tencent_qzone_number_iteration') > 0:
        if len(numbers) >= 10000:
            return numbers
        else:
            numbers.append(r.rpop('tencent_qzone_number_iteration'))
    return numbers


def main(numbers):
    signnumber = {"number":"", "password":""}
    driver = signin(signnumber)
    temp_friend_dict = {}
    information_list = []
    load_list = []
    for number in numbers:
        load_dict, information_dict, friend_list, driver =load(number, driver, signnumber)
#         print load_dict
#         print information_dict
#         print friend_list
        temp_friend_dict[str(number)] = friend_list
        total_information_dict = dict(load_dict, **information_dict)
        information_list.append(total_information_dict)
        load_list.append(load_dict)
        if len(information_list) > 2000:
            dostore(temp_friend_dict, information_list, load_list)
            temp_friend_dict = {}
            information_list = []
            load_list = []
        time.sleep(10)
    driver.quit()

  
def do():
    logging.basicConfig(filename='logger.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s')
    numbers = popnumbers()
    while len(numbers) > 0:
        main(numbers)
        numbers = popnumbers()

# numbers = ['924785452','281179','99938','391166']
if __name__ == '__main__':
    do()
#     numbers = get_numbers()
#     main(numbers)
