#-*- coding:utf-8 -*-
'''
Created on 2017年4月11日

@author: huangjiaxin
'''
import base64
import requests
import re
import json
import rsa
import binascii
import urllib2
import urllib
import cookielib
import StringIO
import gzip
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import dataEncode
reload(dataEncode)

class SinaSpider(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        
        self.servertime = None
        self.nonce = None
        self.pubkey = None
        self.rsakv = None
        
        self.postdata = None
        self.headers = dataEncode.headers
        
        self.cookiejar = None
    
    def setPostData(self):
        self.postdata = dataEncode.createPostdata(self.username, self.password)
        return self
    
    def enableCookie(self):
        self.cookiejar = cookielib.LWPCookieJar()
        cookie_support = urllib2.HTTPCookieProcessor(self.cookiejar)
        opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
        urllib2.install_opener(opener)
        
    def login(self):
        self.setPostData()
        self.enableCookie()
        loginurl = 'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.15)'
        headers = self.headers
        request = urllib2.Request(loginurl, urllib.urlencode(self.postdata), headers)
        resText = urllib2.urlopen(request).read()
        jsonText = json.loads(resText)
        if jsonText['retcode'] == '0':
            print "Login success!"
            cookies = ';'.join([cookie.name + '=' + cookie.value for cookie in self.cookiejar])
            headers['Cookie'] = cookies
            self.headers = headers
        else:
            print "Login failed"
        return self
    
    def openPage(self, url):
        req = urllib2.Request(url, headers=self.headers)
        text = urllib2.urlopen(req).read()
        return self.unizp(text)
    
    def unizp(self, data):
        data = StringIO.StringIO(data)
        gz = gzip.GzipFile(fileobj=data)
        data = gz.read()
        gz.close()
        return data
    
    def output(self, content):
        with open('temp.html', 'w') as f:
            f.write(content)
        return self

def test():
    client = SinaSpider('user', 'password')
    session = client.login()
#     info = session.openPage('http://weibo.com/1669282904/info')
#     print client.headers['Cookie']
#     client.headers['Cookie'] = 'SINAGLOBAL=2430270282789.939.1465367232636; un=15521047700; YF-V5-G0=c948c7abbe2dbb5da556924587966312; _s_tentry=www.google.com.hk; UOR=gaokao.xdf.cn,widget.weibo.com,www.google.com.hk; Apache=2366965167753.996.1491983936491; ULV=1491983936495:89:4:2:2366965167753.996.1491983936491:1491875689637; YF-Ugrow-G0=9642b0b34b4c0d569ed7a372f8823a8e; SCF=AiIZSEsS_5puCyqN9WwWF7R3sgeDf8L6zrCNeTAx_0hbcnxlg8SMQnQ5oWIPGKJPens7pD8AJqHvJpO0Pv-aAc8.; SUB=_2A2516a4fDeRhGeBP7FQR9CzOyT2IHXVWnpjXrDV8PUNbmtBeLUPTkW824r6EM5dtYtcIzhZmyBeeWhip4Q..; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WW-rvD2EyCESWzyxnMJi.Hu5JpX5K2hUgL.FoqpS0q7ShzEeo22dJLoIEBLxKBLBonLB-BLxKBLBo.L12zLxKnL1hMLBoeLxKqLB-BLBKet; SUHB=0u5h4iDaTcRs07; ALF=1492588748; SSOLoginState=1491983951; wvr=6'
    print  client.headers['Cookie']
#     url = 'http://weibo.com/u/1729370543?refer_flag=1001030103_'
    url = 'http://weibo.cn/u/1729370543?f=search_0'
    info = session.openPage(url)
    client.output(info)
    
if __name__ == '__main__':
    test()