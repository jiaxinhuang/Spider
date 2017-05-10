#-*- coding:utf-8 -*-
'''
Created on 2017年4月11日

@author: huangjiaxin
'''
import requests
from bs4 import BeautifulSoup
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def getPage(url):
    response = requests.get(url)
    content = response.text
    return content
#     print content


def catchInformation(content):
    soup = BeautifulSoup(content, 'lxml')
    groupList = soup.find(name='div', attrs={'class':'group-list'})
    for group in groupList.find_all(name='div', attrs={'class':'result'}):
        groupName = str(group.h3.a.text)
        groupLink = str(group.h3.a['href'])
        if "广州" in groupName:
            with open('group-guangzhou.txt', 'a') as file:
                file.write(groupName + ',' + groupLink + '\n')


if __name__ == '__main__':
    for i in range(0, 701, 20):
        url = 'https://www.douban.com/group/explore?start=' + str(i) + '&tag=%E7%A7%9F%E6%88%BF'
        content = getPage(url)
        catchInformation(content)