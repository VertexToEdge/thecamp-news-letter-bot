import requests
import os
import base64
from urllib import parse
import datetime

MOYA_AI_API_TOKEN = os.environ.get('MOYA_AI_API_TOKEN')
THECAMP_EMAIL = os.environ.get('THECAMP_EMAIL')
THECAMP_PASSWORD = base64.b64decode( os.environ.get('THECAMP_PASSWORD')).decode('utf-8')
TRAINEES = [
    {
        "name": "홍길동",
        "traineeMgrSeq":1111111,
        "trainUnitCd":20220211111,
        "trainUnitEduSeq":11111,
    }
]

CATEGORIES = ["IT/인터넷/통신","경제","영화/뮤직","문화","스포츠"]
PAGE_PER_CATEGORY = 3

def moya_news(category, page=1, limit=10):
    API_HOST = "https://api.moya.ai/v2/news"

    data = {
        "token": MOYA_AI_API_TOKEN,
        "limit": limit,
        "page": page,
        "category": [category],
    }

    response = requests.post(API_HOST, json=data)
    return response.json()

def news_generator(category=""):
    page = 1
    news = []
    while True:
        if len(news) == 0:
            t = moya_news(category, page=page, limit=10)
            print(t)
            news += t["datas"]
            page += 1

        yield news.pop(0)

def make_news_entity(news):
    result = ""
    result += f"[{news['mediaName']}]" + news["title"] + " - " + news["publishDate"] + "\r\n"
    result += news["summarized"]
    return result

def make_letter(category, page, line=25, length=1500):
    result = []
    body = ""
    news = news_generator(category)
    for i in range(page):
        n = next(news)
        while True:
            news_entity = make_news_entity( next(news) )
            if len(body) + len(news_entity) > length or str(body+"\n"+news_entity).count("\n") > line:
                break
            if body == "":
                body += news_entity
            else:
                body += "\r\n\r\n" + news_entity
        result.append(body)
    return result

def thecamp_login(session, id, pw):
    url = "https://www.thecamp.or.kr/login/loginA.do"
    id = parse.quote(id)
    pw = parse.quote(pw)
    payload = "state=email-login&autoLoginYn=N&withdrawDate=&withdrawReason=&reCertYn=&telecomCd=&telecomNm=&osType=&osVersion=&deviceModel=&appVersion=&deviceWidth=&deviceHeight=&resultCd=&resultMsg=&findPwType=pwFind&userId=" + id + "&userPwd=" + pw
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'ko,en;q=0.9,en-US;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.thecamp.or.kr',
        'referer': 'https://www.thecamp.or.kr/login/viewLogin.do',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.70',
        'x-requested-with': 'XMLHttpRequest'
    }

    response = session.request("POST", url, headers=headers, data=payload)

    if response.json()["resultCd"] == "0000":
        return True
    return False

def thecamp_send_letter(session, title,body, trainee):
    title = parse.quote(title)

    body = "<p>" + "</p><p>".join(body.split("\r\n")) + "</p>"
    body = parse.quote(body)

    url = "https://www.thecamp.or.kr/consolLetter/insertConsolLetterA.do"

    payload = f"boardDiv=sympathyLetter&tempSaveYn=N&sympathyLetterEditorFileGroupSeq=&fileGroupMgrSeq=&fileMgrSeq=&sympathyLetterMgrSeq=&traineeMgrSeq={trainee['traineeMgrSeq']}&sympathyLetterContent={body}&trainUnitCd={trainee['trainUnitCd']}&trainUnitEduSeq={trainee['trainUnitEduSeq']}&sympathyLetterSubject={title}"
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'ko,en;q=0.9,en-US;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.thecamp.or.kr',
        'referer': 'https://www.thecamp.or.kr/consolLetter/viewConsolLetterInsert.do',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.70',
        'x-requested-with': 'XMLHttpRequest'
    }

    response = session.request("POST", url, headers=headers, data=payload)
    if response.json()["resultCd"] == "0000":
        return True
    return False

session = requests.Session()
if thecamp_login(session, THECAMP_EMAIL, THECAMP_PASSWORD):
    print("로그인 성공")
    for category in CATEGORIES:
        pages = make_letter(category, PAGE_PER_CATEGORY)
        for trainee in TRAINEES:
            for page_num in range(len(pages)):
                title = f"{datetime.datetime.today().strftime('%Y-%m-%d') }[{category}] 뉴스레터 - {page_num+1}"
                if thecamp_send_letter(session, title, pages[page_num], trainee):
                    print(f"성공:  {title} {trainee['name']}")
                else:
                    print(f"실패:  {title} {trainee['name']}")
else:
    print("로그인 실패")
