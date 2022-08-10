import json, requests
import os
from num_for_check import *
from similarity_checker import *
from bs4 import BeautifulSoup
import api_key
import random

use_original_name = 0
youtube_api_key = api_key.YOUTUBE_API_KEY

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
        
    searchKeyword = ""
    
    resolve_info_list = event["context"]["supportedInterfaces"]["Extension"]["data"]["applicationList"]
    print("[resolve_info_list] ", resolve_info_list)
    
    max_similarity = 0
    most_similar_app_name = ""
    most_similar_idx = -1
    pkg = ""
    final_pkg = ""
    play_type = None

    if  action == "action.search.app":
        searchKeyword = event["action"]["parameters"]["searchKeyword"]["value"]
    elif action == "action.mediaplay.app":
        searchKeyword = event["action"]["parameters"]["playKeyword"]["value"]
        
    if action == "action.execute.app":
        appName = event["action"]["parameters"]["appName"]["value"]
    elif action == "action.search.app":
        appName = event["action"]["parameters"]["searchAppName"]["value"]
    elif action == "action.mediaplay.app":
        try:
            appName = event["action"]["parameters"]["playAppName"]["value"]
        except:
            play_type = event["action"]["parameters"].get("playType")
            print("[play_type]", play_type)
            if play_type is not None:
                play_type = play_type["value"]
        
    if  action not in ["action.exit.app"]:
        if appName != "":
            for idx, resolve_info in enumerate (resolve_info_list) :
                app_name_compared = resolve_info["appName"]
                similarity = similarity_checker().find_similarity(appName, app_name_compared)
                    
                if similarity >= MATCH_THRESHOLD and similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_app_name = app_name_compared
                    most_similar_idx = idx
                    if similarity >= COMPLETE_MATCH : break

        if most_similar_idx == -1:
            pkg = search_app_on_market(appName)
            print("[found pkg]", pkg)
        
            for idx, resolve_info in enumerate(resolve_info_list):
                if pkg == resolve_info["packageName"]:
                    final_pkg = resolve_info["packageName"]
                    most_similar_idx = idx
                    most_similar_app_name = resolve_info["appName"]
                    break

        
    # targetUri = getExecUri    action, appName, searchKeyword) 
    if most_similar_app_name == "" : most_similar_app_name = appName
    targetUri = getExecUri(most_similar_idx, resolve_info_list, action, appName, searchKeyword, most_similar_app_name, final_pkg, play_type)
    
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

def getExecUri(idx, resolve_info_list, action, app_name, keyword, most_similar_name, final_pkg, play_type):
    
    global use_original_name
    
    if action == "action.mediaplay.app":
        if app_name.lower() == "youtube" or ((play_type is None or play_type == "영상") and final_pkg == ""):
            print("[final pkg]", final_pkg)
            return media_play_youtube(keyword)
        else:
            return media_play_music(keyword, final_pkg, app_name)
            
    elif action == "action.execute.app":
        if idx == -1 : return
        return resolve_info_list[idx]["intentList"][0]["intentInfo"]["intent"]
        
    elif action == "action.search.app":
        tmp_uri = ""
        
        if idx != -1 :
            for map_string in ["map", "지도", "맵"] :
                if map_string in app_name.lower() and app_name != "지도":
                    pkg = resolve_info_list[idx]["packageName"]
                    uri = "intent:0,0?q={}#Intent;scheme=geo;package={};end".format(keyword, pkg)
                    return uri
                
        
        for info in resolve_info_list[idx]["intentList"]:
            if "SEARCH" in info["intentInfo"]["intent"] :
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
    
    return None

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

def media_play_youtube(query):
    
    intent_uri = ""
    headers = {'User-Agent':'Mozilla/5.0'}
    count = 5
    
    url = "https://www.googleapis.com/youtube/v3/search?key={}&maxResults={}&part=id&type=video&q={}".format(youtube_api_key, count, query)
    response = requests.get(url, headers = headers)
    
    tmp = json.loads(response.text)
    
    if len(tmp["items"]) != 0:
        videoId = random.choice(tmp["items"])["id"]["videoId"]
        intent_uri = "intent://m.youtube.com/watch?v={}#Intent;scheme=https;end".format(videoId)
    
    return intent_uri

def media_play_music(query, pkg, app_name):
    
    intent_uri = ""
    
    if query != "" and (pkg in TMP_MUSIC_APP_LIST or app_name == ""):
        if pkg != "":
            intent_uri = "intent:#Intent;action=android.media.action.MEDIA_PLAY_FROM_SEARCH;package={};S.query={};S.android.intent.extra.focus=vnd.android.cursor.item%2F*;end".format(pkg, query)
        else:
            intent_uri = "intent:#Intent;action=android.media.action.MEDIA_PLAY_FROM_SEARCH;S.query={};S.android.intent.extra.focus=vnd.android.cursor.item%2F*;end".format(query)
    return intent_uri

        