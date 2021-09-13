from urllib import request
from urllib.parse import urlsplit, parse_qs, urlencode
import json
import time
import hashlib
import base64
from aliyunOSS.OSS_download import AliyunOSS
from aliyunOSS.setting import email, password
from os import path
import os

class DownloadBGIData():
    appId = "rAoOnNKg"
    appKey = "C2B37B7A7C69BBD4F635E1FEE957BD1DF11F8C7B"
    getTimestamp_url = "http://8.129.15.0/open/service/timestamp"
    login_url = "http://8.129.15.0/api/user/user/login/verify"
    getProjectId_url = "http://8.129.15.0/api/project/projects/delivered?page=1&pageSize=30"
    def __init__(self, baseDir):
        self.opener =  request.build_opener()
        self.baseDir = baseDir
        self.authStr = ""
        """项目信息"""
        self.projectInfo = {}



    def handle_header(self, req):

        req.add_header('User-Agent', 'Java/1.8.0_261')

        """没有这个会报客户端版本已过时"""
        req.add_header('Client-Version', "202108251433")

        timestamp = int(round(time.time() * 1000))
        req.add_header('App', f"appId={self.appId}&timestamp={timestamp}")
        url_split_res = urlsplit(req.get_full_url())

        uri = url_split_res.path
        query = url_split_res.query
        params = {
            "appId":self.appId,
            "timestamp": timestamp,
            "url":uri
        }
        if query :
            for k,v in parse_qs(url_split_res.query).items():
                params[k] = v[0]
        if req.data:
            req.add_header('Content-Type', 'application/json')
            params["body"] = req.data.decode('utf-8')

        if self.authStr:
            req.add_header('Auth', self.authStr)
            params["token"] = self.tokenData["token"]
            params["userId"] = self.tokenData["userId"]

        params_keys = list(params.keys())

        """对key进行升序排序"""
        params_keys.sort()

        params_list = []
        for k in params_keys :
            params_list.append(f"{k}={params[k]}")

        params_str = "&".join(params_list)
        # 生密钥加密前的字符串
        sign_str = f"{self.appKey}{params_str}"
        # print(f"密钥字符串：{sign_str}")
        """将字符串进行md5加密"""
        Sign = hashlib.md5(sign_str.encode(encoding='UTF-8')).hexdigest().upper()
        req.add_header('Sign', Sign)




    def login(self):
        #  清空
        self.authStr = ""
        jsonData = {
            "email": base64.b64encode(email.encode()).decode(),
            "password": hashlib.sha256(password.encode()).hexdigest().lower()
        }
        req = request.Request(self.login_url, json.dumps(jsonData).encode("utf-8"))

        self.handle_header(req)
        res = self.opener.open(req)
        json_data = json.loads(res.read().decode())
        print(json_data)
        """token 的过期时间是1小时"""
        self.tokenData = json_data["result"]




        auth_str = f"userId={self.tokenData['userId']}&token={self.tokenData['token']}"
        # auth_str = f"userId={userId}&token={token}"
        # print(auth_str)

        self.authStr = base64.b64encode(auth_str.encode()).decode()
        # base64.encode()

        print(f"\n#### 登录成功 ###\n密钥：{self.authStr}")

    def getTimestamp(self):
        req = request.Request(self.getTimestamp_url)
        self.handle_header(req)
        res = self.opener.open(req)
        json_data = json.loads(res.read().decode())
        print(json_data)





    def getProjectInfo(self):
        req = request.Request(self.getProjectId_url)
        self.handle_header(req)
        res = self.opener.open(req)
        result = json.loads(res.read().decode())["result"]

        self.projectInfo["projectNum"] = result["total"]

        """这里认为只有一个project"""
        result = result["list"][0]
        self.projectInfo["projectId"]  = result["projectId"]
        self.projectInfo["projectName"]  = result["projectName"]
        self.projectInfo["rawDataSize"]  = result["rawDataSize"]

        print(f"\n#### 项目信息 ####\n项目ID：{result['projectId']}\n项目名称：{result['projectName']}\n数据大小：{result['rawDataSize']/(1024.0**3)} GB")

    def handleFileInfo(self, file_list):
        """文件过滤"""
        file_list = [i for i in file_list if i["suffix"] == "fq.gz" or i["suffix"] == "md5sum" ]
        f_data = []
        for i, v in enumerate(file_list):
            myObj = {}
            myObj["name"] = v["name"]
            myObj["szie"] = v["fileSize"]
            myObj["path"] = v["path"]
            myObj["fileId"] = v["fileId"]
            myObj["projectId"] = v["projectId"]
            f_data.append(myObj)

        self.fileInfoList = f_data
        # print(self.fileInfoList)



    def getFileInfo(self):
        """获取文件信息，文件名称，大小，存放位置"""
        getFileList_url = f"http://8.129.15.0/api/file/file/{self.projectInfo['projectId']}/delivery/list"
        req = request.Request(getFileList_url)
        self.handle_header(req)
        res = self.opener.open(req)
        result = json.loads(res.read().decode())["result"]
        self.handleFileInfo(result)

    def getDownloadToken(self, fileInfo):
        """获取文件下载token"""
        projectId = fileInfo["projectId"]
        fileId = fileInfo["fileId"]
        url = f"http://8.129.15.0/api/file/file/{projectId}/getDownloadToken/{fileId}"
        req = request.Request(url)
        self.handle_header(req)
        res = self.opener.open(req)
        result = json.loads(res.read().decode())["result"]
        return result

    def downloadFile(self, fileInfo):
        filePath = path.join(self.baseDir, fileInfo["path"].replace("/", ""))
        if not path.exists(filePath):
            os.mkdir(filePath)
        filename = path.join(filePath, fileInfo["name"])
        print(f"\n#### 正在下载以下文件 ####\n保存路径：{filename}")

        if path.exists(filename):
            print("文件已经存在")
            return



        self.login()


        # 这里估计可以同时获取多个文件的token
        downloadToken = self.getDownloadToken(fileInfo)[0]
        stsAccessKeyId = downloadToken["stsAccessKeyId"]
        stsAccessKeySecret = downloadToken["stsAccessKeySecret"]
        stsToken = downloadToken["stsToken"]
        bucket = downloadToken["bucket"]
        objectKey = downloadToken["objectKey"]


        """这里的请求已经是阿里云的对象存储OSS服务器了 """
        # 文档：https://help.aliyun.com/document_detail/32026.htm?spm=a2c4g.11186623.0.0.401f2cea0ptZZW#concept-32026-zh
        aliyun_oss = AliyunOSS(stsAccessKeyId, stsAccessKeySecret, stsToken, objectKey, bucket)
        aliyun_oss.resumableDownload(filename=filename, num_threads=32)



    def doRequest(self, req):

        res = self.opener.open(req)

        return res


    def doRequestTry(self, req):
        while True:
            try:
                return self.doRequest(req)
            except Exception as e:
                print(e)
                time.sleep(0.5)
                self.login()








if __name__ == '__main__':
    baseDir = "/userData/xjm/genome_seq_Po/patch1"
    dd = DownloadBGIData(baseDir)
    # 登录
    dd.login()
    # 获取项目信息
    dd.getProjectInfo()
    # 获取文件信息
    dd.getFileInfo()
    # 下载全部文件
    for i in dd.fileInfoList:
        dd.downloadFile(i)

