#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import logging
import datetime
import boto3
import pickle
import time
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from DataIO import DataIO

class TextRecognize:

    brand_list = {}
    # Patterns of data fields
    # [regex, group_number]
    regex = {
        "Name":     [r"((Name)([^\.:\n]*[\.: \n]+)|(商品名|名称)([^\.:\n]*[\.: \n]+)?)(\n?[ a-zA-Z0-9\-\/\(\)]*[0-9][ a-zA-Z0-9\-\/\(\)]*)[ \n]", 6],
        "Model":    [r"((MODEL|Model)([^\.:\n]*[\.\/: \n]+)|(型名|型番|品番|モデル)([^\.:\n]*[\.: \n]+)?)(\n?[ a-zA-Z0-9\-\/\(\)]*[0-9][a-zA-Z0-9\-\/\(\)]*)[ \n]", 6],
        "Serial":   [r"((SN|S/N|SerialNo|Ser\.No|Serial)([^\.:\n]*[\.: \n]+)|(製造番号)([^\.:\n]*[\.: \n]+)?)(\n?[ a-zA-Z0-9\-\/\(\)]*[0-9][ a-zA-Z0-9\-\/\(\)]*)[ \n]", 6],
    }

    regex_alphanumeric = [
        r"[ :]*([a-zA-Z0-9\-\/\(\)]*[0-9][a-zA-Z0-9\-\/\(\)]*)[ ,.]*", 1]

    def __init__(self, *args, **kwargs):
        # with open('BrandList.json', 'r') as file_json:
        #     self.brand_list = json.load(file_json)
        self.io = DataIO()
        self.brand_list = self.io.get_brandlist()

    def recognize(self, google_text_result):
        ret = {
            "Brand":    [],  # ブランド
            "Name":     [],  # 商品名
            "Model":    [],  # 品番
            "Serial":   [],  # 製造番号
            "NUMBER":   [],  # 備品管理番号
            "Other":    [],  # 候補として他の認識したの英数字
        }

        if google_text_result == {}: return ret

        # Brand recognize
        for brand_name in self.brand_list.keys():
            for brand_text in self.brand_list[brand_name]:
                if re.search(brand_text, google_text_result["text"], re.MULTILINE | re.IGNORECASE):
                    ret["Brand"].append(brand_name)
                    break
                else:
                    for logo in google_text_result["logos"]:
                        if re.search(brand_text, logo, re.MULTILINE | re.IGNORECASE):
                            ret["Brand"].append(brand_name)
                            break

        # Fields Recognize
        for field in self.regex.keys():
            try:
                ret[field].append(re.search(self.regex[field][0], google_text_result["text"], re.MULTILINE | re.IGNORECASE).group(
                    self.regex[field][1]).strip(')'))
            except (AttributeError, IndexError):
                pass

        # Fallback Recognize
        for itr in re.finditer(self.regex_alphanumeric[0], google_text_result["text"], re.MULTILINE):
            str = itr.group(self.regex_alphanumeric[1])
            if (str not in ret.values()) and (len(str) > 2):
                ret["Other"].append(str)
        
        # Equipment Management Number Recognize
        pattern = r'(?<!\()\b(?![a-zA-Z0-9\-\_]{2}\b)(?!\d\b)[a-zA-Z0-9\-\_]*[0-9][a-zA-Z0-9\-\_]*\b(?!>)'
        matches = re.findall(pattern, google_text_result["text"])
        for match in matches:
            ret["NUMBER"].append(match)
        
        return ret

    def match_recognize(self, google_text_result):
        _RE_time = time.time()
        reg_result = self.recognize(google_text_result)
        RE_tokenize_time = time.time()- _RE_time
        
        _fuzzy_db_time = time.time()
        fuzzy_results = self.io.search_fuzzy_model_multiple(reg_result["Model"] + reg_result["Other"])
        reg_result["finded_model"] = {}
        try:
            for (fuzzy_result, fuzzy_ratio) in fuzzy_results.items():
                match_results = self.io.get_product_by_model(fuzzy_result)
                
                for model in match_results:
                    reg_result["finded_model"][model['product']['id']] = model;
                
                # for match_result in match_results:
                #     matched_brand = match_result["manufacturer"]["name"]
                #     if (matched_brand in reg_result["Brand"]) and (fuzzy_result not in reg_result["Model"]):
                if (fuzzy_result not in reg_result["Model"]):
                    reg_result["Model"].append(fuzzy_result)
                        # break
        except IndexError:
                print ("Index Error")
        fuzzy_searching_db_time = time.time() - _fuzzy_db_time
        return reg_result, len(reg_result["Model"])+len(reg_result["Other"]), len(fuzzy_results), RE_tokenize_time, fuzzy_searching_db_time