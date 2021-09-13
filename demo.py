from urllib import request
from urllib.error import HTTPError
from urllib.parse import urlsplit, parse_qs, urlencode
import json
import time
import hashlib
import base64
from aliyunOSS.OSS_download import AliyunOSS
from aliyunOSS.setting import email, password
from os import path
import os

login_url = "http://8.129.15.0/api/user/user/login/verify"
def doRequest():
    opener = request.build_opener()
    jsonData = {
        "email": base64.b64encode(email.encode()).decode(),
        "password": hashlib.sha256(password.encode()).hexdigest().lower()
    }
    req = request.Request(login_url, json.dumps(jsonData).encode("utf-8"))
    # res = opener.open(req)
    # res = opener.open(req)

    try:
        res = opener.open(req)
    except HTTPError as e:
        print(e)
        print(e.fp.read().decode())
        print(f"\n#### 请求头 ####\n{e.headers}")
        return
    json_data = json.loads(res.read().decode())
    print(json_data)


if __name__ == '__main__':
    doRequest()