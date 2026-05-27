#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import json
import uuid
import time

import psycopg2
import ulid
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

import DBInfo

# Class for Data IO and file organize
# May be changed into DB IO


class DataIO:
    #db_info = json.load(open('db-info.json', 'r'))
    db_info = DBInfo.get_db_info()

    input_dir = "Labels"
    output_csv = "result.csv"
    csv_header = []

    db_user_id = "00000000-0000-0000-0000-000000000000"

    def __init__(self):
        # self.f_csv = open(self.output_csv, 'w')
        # self.h_csv = csv.writer(self.f_csv, quoting=csv.QUOTE_ALL)
        # connection to db
        self.conn = psycopg2.connect(database=self.db_info['database'], user=self.db_info['user'],
                                     password=self.db_info['password'], host=self.db_info['server'], port=self.db_info['port'])
        self.cur = self.conn.cursor()
        # self.refresh_models()

    def __del__(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()
        # self.f_csv.close()

    def refresh_models(self):
        self.models = []
        self.cur.execute(
            "SELECT model_name FROM m_products"
        )
        db_results = self.cur.fetchall()
        for db_result in db_results:
            self.models.append(db_result[0])

    def get_time(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def get_brandlist(self):

        brandlist = json.load(open('BrandList.json', 'r'))

        # self.cur.execute(
        #     # "SELECT name, keyword FROM m_manufacturers"
        #     "SELECT name FROM m_manufacturers"
        # )
        # db_results = self.cur.fetchall()
        # brandlist = {}
        # for db_result in db_results:
        #     brandlist[db_result[0]] = []
        #     #keywords = db_result[1].split("|")
        #     # for keyword in keywords:
        #     #     brandlist[db_result[0]].append(keyword)
        return brandlist

    def get_manufacturer_by_name(self, manufacturer_name):
        self.cur.execute(
            "SELECT id, name FROM m_manufacturers WHERE name LIKE '%%%s%%'" % manufacturer_name
        )
        db_results = self.cur.fetchall()
        result = []
        for db_result in db_results:
            result.append({
                "id": db_result[0],
                "name": db_result[1]
            })
        return result

    def get_category_by_id(self, id):
        _item_category = []
        _item_category_id = []
        while True:
            self.cur.execute(
                "SELECT name, parent_id FROM m_item_categories WHERE id = '%s'" % id)
            (_name, _parent) = self.cur.fetchall()[0]
            _item_category.insert(0, _name)
            _item_category_id.insert(0, int(id))
            id = _parent
            if _parent == None:
                break
        return {
            "id": _item_category_id,
            "name": _item_category
        }

    def get_brand_by_name(self, brand_name):
        self.cur.execute(
            "SELECT id, name, keyword FROM m_manufacturers WHERE name = '%s'" % brand_name.replace("'", "''"))
        try:
            db_result = self.cur.fetchall()[0]
            return {
                "id": db_result[0],
                "name": db_result[1],
                "keywords": db_result[2].split('|')
            }
        except IndexError:
            return None
            
    def get_product_by_model(self, model):
        self.cur.execute(
            "SELECT id, name, manufacturer_id, model_name, item_category_id, jan_cd FROM m_products WHERE deleted_at IS NULL AND model_name LIKE '%%%s%%'" % model)
        db_results = self.cur.fetchall()
        result = []
    
        for db_result in db_results:
            _tags = self.get_tags_by_product_id(db_result[0])
            man_id, cat_id = db_result[2], db_result[4]
    
            product = {
                "id": db_result[0],
                "jan_cd": db_result[5],
                "name": db_result[1],
                "model_name": db_result[3],
                "tags": _tags
            }
    
            manufacturer = {
                "id": 0,
                "name": "null"
            }
    
            if man_id:
                self.cur.execute(
                    "SELECT name FROM m_manufacturers WHERE id = '%s'" % db_result[2])
                _manufacturer_name = self.cur.fetchall()[0]
                manufacturer = {
                    "id": db_result[2],
                    "name": _manufacturer_name[0]
                }
    
            result.append({
                "product": product,
                "manufacturer": manufacturer,
                "model": db_result[3]
            })
    
        return result

    # def get_product_by_model(self, model):
    #     self.cur.execute(
    #         "SELECT id, name, manufacturer_id, model_name, item_category_id, jan_cd FROM m_products WHERE deleted_at IS NULL AND model_name LIKE '%%%s%%'" % model)
    #     db_results = self.cur.fetchall()
    #     result = []
    #     print (len(db_results))
    #     for db_result in db_results:
    #         #logger.info(db_result[2])
    #         man_id, cat_id = db_result[2], db_result[4]
    #         if not man_id and not cat_id:
    #             logger.info(db_result[2])
    #             result.append({
    #                 "product": {
    #                     "id": db_result[0],
    #                     "jan_cd": db_result[5],
    #                     "name": db_result[1],
    #                     "model_name": db_result[3],
    #                     "category_l_id":0,
    #                     "category_l_name":"null",
    #                     "category_m_id":0,
    #                     "category_m_name":"null",
    #                     "category_s_id":0,
    #                     "category_s_name":"null"
    #                 },
    #                 "manufacturer": {
    #                     "id": 0,
    #                     "name": "null"
    #                 },
    #                 "category": 0,
    #                 "model": db_result[3]
    #             })
    #         elif not man_id and cat_id:
    #             _category = self.get_category_by_id(db_result[4])
    #             result.append({
    #                 "product": {
    #                     "id": db_result[0],
    #                     "jan_cd": db_result[5],
    #                     "name": db_result[1],
    #                     "model_name": db_result[3],
    #                     "category_l_id":_category["id"][0],
    #                     "category_l_name":_category["name"][0],
    #                     "category_m_id":_category["id"][1],
    #                     "category_m_name":_category["name"][1],
    #                     "category_s_id":_category["id"][2],
    #                     "category_s_name":_category["name"][2]
    #                 },
    #                 "manufacturer": {
    #                     "id": 0,
    #                     "name": "null"
    #                 },
    #                 "category": _category,
    #                 "model": db_result[3]
    #             })
    #         elif man_id and not cat_id:
    #             logger.info(db_result[2])
    #             self.cur.execute(
    #                 "SELECT name FROM m_manufacturers WHERE id = '%s'" % db_result[2])
    #             _manufacturer_name = self.cur.fetchall()[0]
    #             result.append({
    #                 "product": {
    #                     "id": db_result[0],
    #                     "jan_cd": db_result[5],
    #                     "name": db_result[1],
    #                     "model_name": db_result[3],
    #                     "category_l_id":0,
    #                     "category_l_name":"null",
    #                     "category_m_id":0,
    #                     "category_m_name":"null",
    #                     "category_s_id":0,
    #                     "category_s_name":"null"
    #                 },
    #                 "manufacturer": {
    #                     "id": db_result[2],
    #                     "name": _manufacturer_name[0]
    #                 },
    #                 "category": 0,
    #                 "model": db_result[3]
    #             })    
    #         else:
    #             # get manufacturer name
    #             self.cur.execute(
    #                 "SELECT name FROM m_manufacturers WHERE id = '%s'" % db_result[2])
    #             _manufacturer_name = self.cur.fetchall()[0]
    #             # get item_category
    #             _category = self.get_category_by_id(db_result[4])
    #             result.append({
    #                 "product": {
    #                     "id": db_result[0],
    #                     "jan_cd": db_result[5],
    #                     "name": db_result[1],
    #                     "model_name": db_result[3],
    #                     "category_l_id":_category["id"][0],
    #                     "category_l_name":_category["name"][0],
    #                     "category_m_id":_category["id"][1],
    #                     "category_m_name":_category["name"][1],
    #                     "category_s_id":_category["id"][2],
    #                     "category_s_name":_category["name"][2]
    #                 },
    #                 "manufacturer": {
    #                     "id": db_result[2],
    #                     "name": _manufacturer_name[0]
    #                 },
    #                 "category": _category,
    #                 "model": db_result[3]
    #             })
    #     return result

    def search_fuzzy_model(self, keyword, fuzzy_threshold = 70):
        ratios = {}
        for model in self.models:
            _ratio = fuzz.ratio(keyword, model)
            if _ratio >= fuzzy_threshold:
                ratios[model] = _ratio
        return {k: v for k, v in sorted(ratios.items(), key=lambda i: i[1], reverse=True)}

    def search_fuzzy_model_by_like(self, keyword, fuzzy_threshold = 70):
        ratios = {}

        term= keyword.replace('=', '==').replace('%', '=%').replace('_', '=_')
        #logger.info("keyword modification")
        #logger.info(term)
        #model_keywords = self.chen_idea(term)
        

        self.cur.execute(
            "SELECT model_name FROM m_products WHERE deleted_at IS NULL AND model_name LIKE %(like)s ESCAPE '='",
            dict(like= term+'%')
        )

        db_results = self.cur.fetchall()
        #logger.info("DB result before Fuzzy ratio:")
        #logger.info(db_results)
        #print ("DB matches", db_results)
        
        for db_result in db_results:
            _ratio = fuzz.ratio(keyword, db_result[0])
            #logger.info("Fuzzy ratio :")
            #logger.info(_ratio)
            if _ratio >= fuzzy_threshold:
                ratios[db_result[0]] = _ratio
        return {k: v for k, v in sorted(ratios.items(), key=lambda i: i[1], reverse=True)}
    
    def search_fuzzy_model_multiple(self, keywords: list, count=5, fuzzy_threshold = 50):
        dict_ratios_top = {}
        #logger.info("Fuzzy Search keywords")
        #logger.info(keywords)
        #print ("keywords", keywords)
        #for keyword in keywords:
            #dict_single_ratios = self.search_fuzzy_model_by_like(keyword, fuzzy_threshold)
            #logger.info("Return fuzzy model -> "+ str(keyword))
            #logger.info(dict_single_ratios)
        for keyword in keywords:
            
            start_time = time.time()
            dict_single_ratios = self.search_fuzzy_model_by_like(keyword, fuzzy_threshold)
            print ("Ratios", dict_single_ratios)
            #print("--- like query for keyword  %s ---" % keyword)
            #print("--- %s seconds ---" % (time.time() - start_time))
            
            r_count = min(len(dict_single_ratios), count)
            for _pair in list(dict_single_ratios.items())[:r_count]:
                # keep the higher ratio in the dictonary
                if dict_ratios_top.get(_pair[0], -1) < _pair[1]:
                    dict_ratios_top[_pair[0]] = _pair[1]
                    
            if dict_ratios_top:
                break

        return {k: v for k, v in sorted(dict_ratios_top.items(), key=lambda i: i[1], reverse=True)}


    def update_keyword_by_id(self, manufacturer_id, keyword):
        return self.cur.execute(
            "UPDATE m_manufacturers SET keyword='%s' WHERE id='%s'" %
            (keyword, manufacturer_id)
        )

    def add_item(self, item_name, manufacturer_id, product_id, serial_num):
        _uuid = uuid.uuid4()
        return self.cur.execute(
            "INSERT INTO m_items(id, account_id, item_name, manufacturer_id, product_id, serial_num) VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" %
            (_uuid, '3541', item_name, manufacturer_id, product_id, serial_num))

    def add_brand(self, name, keyword):
        _uuid = uuid.uuid4()
        _time = self.get_time()
        return self.cur.execute(
            "INSERT INTO m_manufacturers(id, name, keyword, created_at, created_user_id, updated_at, updated_user_id) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s')" %
            (_uuid, name.replace("'", "''"), keyword.replace("'", "''"), _time, self.db_user_id, _time, self.db_user_id))

    def add_product(self, name, model_name, manufacturer_id, item_category_id):
        _uuid = uuid.uuid4()
        _time = self.get_time()
        return self.cur.execute(
            "INSERT INTO m_products(id, name, model_name, manufacturer_id, item_category_id, created_at, created_user_id, updated_at, updated_user_id) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" %
            (_uuid, name.replace("'", "''"), model_name.replace("'", "''"), manufacturer_id,
             item_category_id, _time, self.db_user_id, _time, self.db_user_id)
        )

    def get_files(self):
        files_list = []
        for _fpath, _, _files in os.walk(self.input_dir):
            # for all image files in folder
            for _file in _files:
                if _file.split(".")[-1].lower() in ["jpg", "jpeg", "png"]:
                    files_list.append(
                        os.path.join(_fpath, _file))
        return files_list

    def write_result(self, data_dict):
        if len(self.csv_header) == 0:
            self.csv_header = list(data_dict.keys())
            self.h_csv.writerow(self.csv_header)
        self.h_csv.writerow(list(data_dict.values()))
        
    def get_tags_by_product_id(self, product_id):
        self.cur.execute(
            "SELECT m_item_tags.id, m_item_tags.name from m_products join r_product_item_tag_rel on m_products.id = r_product_item_tag_rel.product_id "
            "join m_item_tags on r_product_item_tag_rel.tag_id = m_item_tags.id where m_products.id = '%s'" % product_id
        )
        result = []
        try:
            db_results = self.cur.fetchall()
            for db_result in db_results:
                result.append({
                    "id": str(db_result[0]),
                    "name": db_result[1]
                })
            return result
        except IndexError:
            return result  


if __name__ == "__main__":
    d = DataIO()
    # print(d.get_info_by_model("MC604J/A"))
    # d.add_item('Test Item', '9f505a16-e9d5-4b3e-9207-08e722a59a4c', '5c5749ba-96d0-4508-b12a-74b028f1679b', 'test serial')
    print(d.search_fuzzy_model_multiple(["MD261K/A", "MD246J/A"]))
