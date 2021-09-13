

import oss2
import sys
from tqdm import tqdm
class AliyunOSS():
    def __init__(self, stsAccessKeyId, stsAccessKeySecret, stsToken, objectKey, bucket_name, endpoint='http://oss-cn-shenzhen.aliyuncs.com'):

        self.stsAccessKeyId = stsAccessKeyId
        self.stsAccessKeySecret = stsAccessKeySecret
        self.stsToken = stsToken
        self.bucket_name = bucket_name
        self.objectKey = objectKey
        self.endpoint = endpoint

        # 确认上面的参数都填写正确了
        for param in (stsAccessKeyId, stsAccessKeySecret, stsToken, bucket_name, objectKey, endpoint):
            assert '<' not in param, '请设置参数：' + param
        auth = oss2.StsAuth(stsAccessKeyId, stsAccessKeySecret, stsToken)
        # 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
        self.bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)

    def downloadFile(self, filename):
        result = self.bucket.get_object_to_file(self.objectKey, filename)
        print(result)


    def progressCallback(self, consumed_bytes, total_bytes):
        """进度条回调函数，计算当前完成的百分比
        :param consumed_bytes: 已经上传/下载的数据量
        :param total_bytes: 总数据量
        """
        if total_bytes:
            rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
            if not self.isDownloading:
                self.progress = rate
                self.mytqdm.update(rate)
                self.isDownloading  = True
            else:
                self.mytqdm.update(rate - self.progress)
            self.progress = rate

            self.mytqdm.set_description_str(f"总大小: {round(float(total_bytes)/(1024**2), 2)} MB；已下载: {round(float(consumed_bytes)/(1024**2), 2)} MB")
            """要加\r  还有end=''才能清空"""
            # print(f"\r{rate}%，总大小: {float(total_bytes)/(1024**2)}MB; 已下载: {float(consumed_bytes)/(1024**2)}MB", end="")

            # sys.stdout.flush()


    def resumableDownload(self,filename, num_threads=8):
        self.mytqdm = tqdm(iterable=range(100), ncols=100)
        self.isDownloading = False

        oss2.resumable_download(self.bucket, self.objectKey, filename,
                                multiget_threshold=200 * 1024,
                                part_size=500 * 1024,
                                num_threads=num_threads,
                                progress_callback=self.progressCallback
                                )








