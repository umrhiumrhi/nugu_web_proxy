import json, requests
import os
from num_for_check import *
from similarity_checker import *
from bs4 import BeautifulSoup


use_original_name = 0

def lambda_handler(event, context):
    
    global use_original_name
    use_original_name = 0
    json_object = ""
    appName = ""
    
    print("[original]: ",event)
    
    # post 방식에 의해 event로 넘겨 받았을 때 'body' key 참조
    event = json.loads(event['body'])
    print("[json]: ",event)
    
    action = event["action"]["actionName"]
    
    if action == "action.execute.app":
        appName = event["action"]["parameters"]["appName"]["value"]
    elif action == "action.search.app":
        appName = event["action"]["parameters"]["searchAppName"]["value"]
    
    searchKeyword = ""
    
    resolve_info_list = event["context"]["supportedInterfaces"]["Extension"]["data"]["applicationList"]
    print("[resolve_info_list] ", resolve_info_list)
    
    max_similarity = 0
    most_similar_app_name = ""
    most_similar_idx = -1
    pkg = ""

    
    if  action != "action.exit.app":
        pkg = search_app_on_market(appName)
        print("[found pkg]", pkg)
        
        for idx, resolve_info in enumerate(resolve_info_list):
            if pkg == resolve_info["packageName"]:
                most_similar_idx = idx
                most_similar_app_name = resolve_info["appName"]
                break
                
        if most_similar_idx == -1:
            for idx, resolve_info in enumerate (resolve_info_list) :
                app_name_compared = resolve_info["appName"]
                similarity = similarity_checker().find_similarity(appName, app_name_compared)
                    
                if similarity >= MATCH_THRESHOLD and similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_app_name = app_name_compared
                    most_similar_idx = idx
                    if similarity >= COMPLETE_MATCH : break
        if  action == "action.search.app":
            searchKeyword = event["action"]["parameters"]["searchKeyword"]["value"]
        
    # targetUri = getExecUri    action, appName, searchKeyword) 
    if most_similar_app_name == "" : most_similar_app_name = appName
    targetUri = getExecUri(most_similar_idx, resolve_info_list, action, appName, searchKeyword, most_similar_app_name)
    
    if use_original_name:
        most_similar_app_name = appName
    
    if targetUri is not None:
        json_object = {
          "version": "2.0",
          "resultCode": "OK",
          "output": {
             "appName": most_similar_app_name,
             "action": action,
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

def getExecUri(idx, resolve_info_list, action, app_name, keyword, most_similar_name):
    
    global use_original_name
    
    if action == "action.execute.app":
        if idx == -1 : return
        return resolve_info_list[idx]["intentList"][0]["intentInfo"]["intent"]
        
    elif action == "action.search.app":
        tmp_uri = ""
        
        for info in resolve_info_list[idx]["intentList"]:
            if "WEB_SEARCH" in info["intentInfo"]["intent"] :
                tmp_uri = info["intentInfo"]["intent"].replace(";end", ";S.query="+keyword+";end")
                
        if tmp_uri != "" : return tmp_uri 
        
        with open("app-exec-set.json", 'r', encoding='UTF-8') as file:
            actionDataSet = json.load(file)
        
        execList =  actionDataSet["actionType"][action]

        for data in execList:
            if data['appName'].lower() == app_name.lower():
                use_original_name = 1
                return data['uri'].replace('{search_keyword}', keyword) if keyword != "" else data['uri']
                
    elif action == "action.exit.app":
        return "intent:#Intent;action=android.intent.action.MAIN;category=android.intent.category.HOME;launchFlags=0x4000000;end"
    
    return ""

def search_app_on_market(query):
    
    pkg = ""
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}

    url = "https://play.google.com/store/search?q="+query
    response = requests.get(url, headers = headers)
    
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        first = soup.find("a", attrs={"class" : "Qfxief"})
        if first is not None:
            k = str(first["href"]).find('=')
            pkg = first["href"][k+1:]

        else:
            second = soup.find_all("a", attrs={"class" : "Si6A0c Gy4nib"})[:1]
            for data in second:
                k = str(data["href"]).find('=')     
                pkg = data["href"][k+1:]

    return pkg