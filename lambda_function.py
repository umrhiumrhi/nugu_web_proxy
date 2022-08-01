import json
import os
from num_for_check import *
from similarity_checker import *

def lambda_handler(event, context):
    print("[original]: ",event)
    
    # post 방식에 의해 event로 넘겨 받았을 때 'body' key 참조
    event = json.loads(event['body'])
    print("[json]: ",event)
    
    appName = event["action"]['parameters']['appName']['value']
    appExec = event['action']['parameters']['appExec']['value']
    # searchKeyword = event['searchKeyword']
    searchKeyword = ""
    
    resolve_info_list = event["context"]["supportedInterfaces"]["Extension"]["data"]["applicationList"]
    print("[resolve_info_list] ", resolve_info_list)
    
    max_similarity = 0
    most_similar_app_name = ""
    most_similar_idx = -1
    
    for idx, resolve_info in enumerate (resolve_info_list) :
        app_name_compared = resolve_info["appName"]
        similarity = similarity_checker().find_similarity(appName, app_name_compared)
        
        if similarity >= MATCH_THRESHOLD and similarity > max_similarity:
            max_similarity = similarity
            most_similar_app_name = app_name_compared
            most_similar_idx = idx
            if similarity >= COMPLETE_MATCH : break
    
    # targetUri = getExecUri(appExec, appName, searchKeyword) 
    targetUri = getExecUri(most_similar_idx, resolve_info_list)
    
    if appExec == "검색":
        searchKeyword = event['searchKeyword']
    
    json_object = {
      "version": "2.0",
      "resultCode": "OK",
      "output": {
         "appName": most_similar_app_name,
         "appExec": appExec,
    "searchKeyword": searchKeyword
      },
      "directives": [
         {
            "type": "Extension.Action",
            "version": "1.0",
            "data": {
               "action": "Open.Intent",
               "url": targetUri
            }
         }
      ]
   }
   
    print("[response] ", json_object)
    
    return {
        'statusCode': 200,
        'body': json.dumps(json_object, ensure_ascii=False)
    }

def getExecUri(idx, resolve_info_list):
        return resolve_info_list[idx]["intentList"][0]["intentInfo"]["intent"]
    # with open("app-exec-set.json", 'r', encoding='UTF-8') as file:
    #     appExecDataSet = json.load(file)
    
    # execList = appExecDataSet["actionType"][appExec]
    
    # for data in execList:
    #     if data['appName'] == appName:
    #         return data['uri'].replace('{search_keyword}', searchKeyword) if searchKeyword != "" else data['uri']