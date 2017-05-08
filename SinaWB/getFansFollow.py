#-*- coding:utf-8 -*-
'''
Created on 2017年4月14日

@author: huangjiaxin
'''
from bs4 import BeautifulSoup
import re
import redis
import time

from SinaSpider import SinaSpider

def getFans(content):
    fanIDList = []
    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all(name='table')
    for table in tables:
        td = table.find_all(name='td', attrs={'valign':'top'})[1]
        faner = str(td.find_all(name='a')[-1]['href'])
        fanID = re.findall(r'uid=(\d+?)&', faner)[0]
        fanIDList.append(fanID)
    return fanIDList


def getFollow(content):
    followIDList = []
    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all(name='table')
    for table in tables:
        td = table.find_all(name='td', attrs={'valign':'top'})[1]
        follower = str(td.find_all(name='a')[-1]['href'])
        followID = re.findall(r'uid=(\d+?)&', follower)[0]
        followIDList.append(followID)
    return followIDList


def dostore(idList):
    r = redis.Redis(host='192.168.8.25', port=6379, password='npq8pprjxnppn477xssn', db=0)
    for item in idList:
        r.lpushx('sina_wb_wid', item)
        r.lpushx('sina_wb_wid_iterate', item)


def main():
    r = redis.Redis(host='192.168.8.25', port=6379, password='npq8pprjxnppn477xssn', db=0)
    client = SinaSpider('', '')
    session =client.login()
    client.headers['Cookie'] = '_T_WM=539fba9bfcabb75cce5da4e1f8225929; ALF=1495103271; SCF=AiIZSEsS_5puCyqN9WwWF7R3sgeDf8L6zrCNeTAx_0hb7katXoZ6x53xJ_A0s5CDfR7XqvKJ7fN8LQx2IwdHrUA.; SUB=_2A2518sk_DeRhGeBP7FQR9CzOyT2IHXVXHNd3rDV6PUNbktBeLUzTkW11kOEc7LDLWxcjSknph0oPukXjFA..; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WW-rvD2EyCESWzyxnMJi.Hu5JpX5KMhUgL.FoqpS0q7ShzEeo22dJLoIEBLxKBLBonLB-BLxKBLBo.L12zLxKnL1hMLBoeLxKqLB-BLBKet; SUHB=0gHSxm94OPzv4P'
    try:
        while True:
            userid = r.rpop('sina_wb_wid_iterate')
            if userid:
                url = 'http://weibo.cn/1677856077/fans?page='
                for page in range(1, 11):
                    info = session.openPage(url + str(page))
                    fanIDList = getFans(info)
                    dostore(fanIDList)
                    time.sleep(2)
        
                url = 'http://weibo.cn/1677856077/follow?page='
                for page in range(1, 11):
                    info = session.openPage(url + str(page))
                    followIDList = getFollow(info)
                    dostore(followIDList)
                    time.sleep(2)
            else:
                break
    except Exception, e:
        print Exception,e

if __name__ == '__main__':
    main()