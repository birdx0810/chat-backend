#!/usr/bin/env python
# coding: utf-8

import requests
import re
import configparser
import json
from bs4 import BeautifulSoup
import random

def transformAddress(address, GOOGLE_API_KEY):

    addurl = 'https://maps.googleapis.com/maps/api/geocode/json?key={}&address={}&sensor=false'.format(GOOGLE_API_KEY,address)
    # 經緯度轉換
    addressReq = requests.get(addurl)
    addressDoc = addressReq.json()
    lat = addressDoc['results'][0]['geometry']['location']['lat']
    lng = addressDoc['results'][0]['geometry']['location']['lng']
    return  lat, lng


def content(clinic):
    hospital = []
    # 医院詳細資訊
    rating = "無" if clinic.get("rating") is None else clinic["rating"]
    address = "沒有資料" if clinic.get("vicinity") is None else clinic["vicinity"]
    details = "Google Map評分：{}\n地址：{}".format(rating, address)
    hospital.append(clinic.get("name"))
    hospital.append(details.replace('\n',', '))

    # 取得医院的 Google map 網址
    mapUrl = "https://www.google.com/maps/search/?api=1&query={lat},{long}&query_place_id={place_id}".format(lat=clinic["geometry"]["location"]["lat"],long=clinic["geometry"]["location"]["lng"],place_id=clinic["place_id"])
    hospital.append(mapUrl)
    return hospital

def searchHospital(lat, lng, kw, GOOGLE_API_KEY ,searchtype):
    # 取得附近医院資訊
    clinicSearch = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?key={}&location={},{}&rankby=distance&type={}&keyword={}&language=zh-TW".format(GOOGLE_API_KEY, lat, lng, searchtype, kw)

    clinicReq = requests.get(clinicSearch)
    nearbyclinicReq_dict = clinicReq.json()
    top5clinicReq = nearbyclinicReq_dict["results"]
    res_num = (len(top5clinicReq)) 
    # 取評分高於3.9的医院
    bravo=[]
    for i in range(res_num):
        try:
            if top5clinicReq[i]['rating'] > 3.9:
                bravo.append(i)
        except:
            KeyError
    if len(bravo) < 0:
        print("No clinic or hospital nearby. ")
    
    allhospital = []
    for clinicCode in bravo:
        allhospital.append(content(top5clinicReq[clinicCode]))
    return allhospital
    

def get_hospitals(lat, lng, keyword, GOOGLE_API_KEY='AIzaSyCE-XxvXrHO2rmzhoH5Aud4bKk1Jq5o0bw', searchtype = ''):
    # 经纬度，keyword，apikey，搜索类型例如hospital
    allhospitals = searchHospital(lat, lng, keyword, GOOGLE_API_KEY, searchtype)
    return allhospitals[:5]

def get_address(address, keyword, GOOGLE_API_KEY='AIzaSyCE-XxvXrHO2rmzhoH5Aud4bKk1Jq5o0bw', searchtype = ''):
    # 经纬度，keyword，apikey，搜索类型例如hospital
    lat, log = transformAddress(address, GOOGLE_API_KEY)
    allhospitals = searchHospital(lat, log, Keyword, GOOGLE_API_KEY ,searchtype)
    return allhospitals[:5]
