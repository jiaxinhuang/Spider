# -*- coding:utf-8 -*-
'''
Created on 2017年3月14日

@author: huangjiaxin
'''
import base64
import rsa
import binascii
import requests
import json
import re

headers = {
        "Origin" : "https://login.sina.com.cn",
        "User-Agent" : "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0",
        "Content-Type" : "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer" : "https://login.sina.com.cn/signup/signin.php?entry=sso",
        "Accept-Encoding" : "gzip, deflate, sdch",
        "Accept-Language" : "en-GB,en;q=0.8,zh-CN;q=0.6,zh;q=0.4"
    }

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


def encode_username(username):
    return base64.encodestring(username)[:-1]

def encode_password(password, servertime, nonce, pubkey):
    rsaPubkey = int(pubkey, 16)
    RSAKey = rsa.PublicKey(rsaPubkey, 65537)
    codeStr = str(servertime) + '\t' + str(nonce) + str(password)
    pwd = rsa.encrypt(codeStr, RSAKey)
    return binascii.b2a_hex(pwd)

def get_prelogin_info():
    url = r'https://login.sina.com.cn/sso/prelogin.php?entry=account&callback=sinaSSOController.preloginCallBack&su=MTU1MjEwNDc3MDA%3D&rsakt=mod&client=ssologin.js(v1.4.15)'
    html = requests.get(url).text
    jsonStr = re.findall(r'\((\{.*?\})\)', html)[0]