import json
import time
import datetime
import pytesseract
from TextRecognize import TextRecognize
from GoogleAPI import *
import base64

import DBInfo
import boto3
import pickle
import os
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    
    logger.info('### EVENT START')
    logger.info(event)
    logger.info('### EVENT END')
    try:
        _api_call_time = time.time()
        #event_arr = json.loads(event)
        #if "context" in event:
        #    DBInfo.stage = event["context"]["stage"]
            
        if "file" not in event["body-json"]:
            raise NameError('ファイルが添付されていません')
        
        try:
            decoded_file = base64.b64decode(event["body-json"]['file'])
        except Exception as e:
            raise NameError('ファイルの形式が正しくありません')
         
        try:
            _g_time = time.time()
            google_result = get_vision_result(decoded_file)
            google_ocr_time = time.time() - _g_time
        except Exception as e:
            raise NameError(e)

        if bool( 'text' not in google_result or not google_result["text"] or google_result["text"].isspace()):
            raise NameError("有効な文字情報が見つかりませんでした。明るさや角度を変えて再度撮影するか、手動で入力してください")

        recognizer = TextRecognize()
        
        file_result = recognizer.match_recognize(google_result)
        
        if bool( 'finded_model' not in file_result[0] or not file_result[0]["finded_model"] ):
            raise NameError("対応する製品情報が見つかりませんでした。再度撮影するか、手動で入力してください")

        products = []
        for model in file_result[0]['finded_model']:
            products.append(file_result[0]['finded_model'][model]['product'])
    
        api_total_time = time.time() - _api_call_time
        print ("length, RE, DB", file_result[1], file_result[2], "OCR", google_ocr_time, "RE", file_result[3], "DB", file_result[4], "API total", api_total_time)
    except Exception as e:
        
        logger.error('## LABEL RECOGNIZE error')
        logger.error(str(e))
        
        return {
            'result': "false",
            'errorMessage': str(e),
            #'google_result': google_result,
            #'Regular Expression result':(file_result[0]["Model"],file_result[0]["Other"]),
            #'OCR Time': google_ocr_time,
            #'RE Time': file_result[3],
            #'Total Search': file_result[1],
            #'Total Seventy': file_result[2],
            #'fuzzy_search_time': file_result[4],
            #'API Time': api_total_time,
            #'stage':event["context"],
            #'-':file_result,
        }
    
    logger.info('## SUCCESSFULLY RECOGNIZED LABEL')
    logger.info('## PARCED TEXT')
    logger.info(google_result["text"])
    logger.info('## FINDED PRODUCTS')
    logger.info(products)
    
    return {
            'result': "true",
            'products': products,
            #'stage':event["context"],
            #'google_result': google_result,
            'Serial':file_result[0]["Serial"],
            'Equipment Number': file_result[0]["NUMBER"],
            #'Regular Expression result':(file_result[0]["Model"],file_result[0]["Other"]),
            #'OCR Time': google_ocr_time,
            #'RE Time': file_result[3],
            #'Total Search': file_result[1],
            #'Total Seventy': file_result[2],
            #'fuzzy_search_time': file_result[4],
            #'API Time': api_total_time,
            #'stage': DBInfo.stage,
            #'base64_decode_time': decode_time,
            #'google_vision_time': google_vision_time,
            #'init_recognizer_time': init_recognizer_time,
            #'recognizer_work_time': recognizer_work_time,
            #'google_result': google_result
            
        }    
