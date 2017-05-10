#-*- coding:utf-8 -*-
'''
Created on 2017年4月11日

@author: huangjiaxin
'''
import requests
import time
from bs4 import BeautifulSoup
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

headers = {
           'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
           'Accept-Encoding':'gzip, deflate, sdch, br',
           'Accept-Language':'zh-CN,zh;q=0.8',
           'Connection':'keep-alive',
           'Host':'www.douban.com',
           'Upgrade-Insecure-Requests':'1',
           'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
           }


def getUrl():
    urlList = []
    with open('group-guangzhou.txt', 'r') as file:
        url_line = file.readlines()
    
    for url in url_line:
        link = url.split(',')
        linkTemp = link[1].strip('\n')
        urlList.append(linkTemp)
    return urlList


def getDetail(url):
    response = requests.get(url, headers)
    content = response.text
    soup = BeautifulSoup(content, 'lxml')
    olt = soup.find(name='table', attrs={'class':'olt'})
    for td in olt.find_all(name='td', attrs={'class':'title'}):
        title = str(td.a['title'])
        link = str(td.a['href'])
        with open('detail-guangzhou.txt', 'a') as tempfile:
            tempfile.write(title + ',' + link + '\n')


if __name__ == '__main__':
    urlList = getUrl()
    for url in urlList:
        for num in xrange(5025, 10001, 25):
            pageurl = url + 'discussion?start=' + str(num)
            try:
                getDetail(pageurl)
                time.sleep(3)
            except Exception, e:
                print e