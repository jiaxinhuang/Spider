#-*- coding:utf-8 -*-
'''
Created on 2017年3月20日

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
import sys
reload(sys)
sys.setdefaultencoding('utf8')


def encodeUsername(username):
    return base64.b64encode(username)


def encodePassword(password, servertime, nonce, pubkey):
    rsaPubkey = int(pubkey, 16)
    RSAKey = rsa.PublicKey(rsaPubkey, 65537)
    codeStr = str(servertime) + '\t' + str(nonce) + '\n' + str(password)
    pwd = rsa.encrypt(codeStr, RSAKey)
    return binascii.b2a_hex(pwd)


def getPrelogin(username):
    url = ('https://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=' + username[:-1] + '&rsakt=mod&client=ssologin.js(v1.4.15)')
    html = requests.get(url).text
    content = re.findall('({.*})', html)[0]
    data = json.loads(content)
#     print content
    servertime = data['servertime']
    nonce = data['nonce']
    pubkey = data['pubkey']
    rsakv = data['rsakv']
    return servertime, nonce, pubkey, rsakv


def createPostdata(username, password):
    su = encodeUsername(username)
    servertime, nonce, pubkey, rsakv = getPrelogin(su)
    password_encode = encodePassword(password, servertime, nonce, pubkey)
    post_data = {
                 "cdult":"3",
                 "domain":"sina.com.cn",
                 "encoding":"UTF-8",
                 "entry":"account",
                 "from":"",
                 "gateway":"1",
                 "nonce":str(nonce),
                 "pagerefer":"http://login.sina.com.cn/sso/logout.php",
                 "prelt":"41",
                 "pwencode":"rsa2",
                 "returntype":"TEXT",
                 "rsakv":str(rsakv),
                 "servertime":str(servertime),
                 "service":"account",
                 "sp":str(password_encode),
                 "sr":"1680*1050",
                 "su":str(su),
                 "useticket":"0",
                 "vsnf":"1"
                 }
    return post_data


def enableCookie():
    cookiejar = cookielib.LWPCookieJar()
    cookie_support = urllib2.HTTPCookieProcessor(cookiejar)
    opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
    urllib2.install_opener(opener)
    return cookiejar


def login(post_data, url):
    headers = {
        "Origin" : "https://login.sina.com.cn",
        "User-Agent" : "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0",
        "Content-Type" : "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer" : "https://login.sina.com.cn/signup/signin.php?entry=sso",
        "Accept-Encoding" : "deflate, br",
        "Accept-Language" : "en-GB,en;q=0.8,zh-CN;q=0.6,zh;q=0.4"
    }
    cookiejar = enableCookie()
    request = urllib2.Request(url, urllib.urlencode(post_data), headers)
    resText = urllib2.urlopen(request).read()
    jsonText = json.loads(resText)
    if jsonText['retcode'] == '0':
        cookies = ';'.join([cookie.name + "=" + cookie.value for cookie in cookiejar])
        headers['Cookie'] = cookies
    urltest = 'http://weibo.com/1669282904/info'
    openURL(urltest, headers)


def openURL(url, headers):
    req = urllib2.Request(url, headers=headers)
    text = urllib2.urlopen(req).read()
    print text


if __name__ == '__main__':
    username = '15521047700'
    password = '924785452zz'
    url = r'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.15)'
    post_data = createPostdata(username, password)
    login(post_data, url)