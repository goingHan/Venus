#!/usr/bin/env python
# encoding: utf-8
import threadpool
import traceback
from multiprocessing.queues import Empty
try:
    from bin.base import BaseObject
    from bin.dealSftp import SftpOperate
    from bin.dealFtp import FtpOperate
    from bin.dealLocal import LocalOperate
    from bin.oneMore import OneMore
except ModuleNotFoundError:
    from base import BaseObject
    from dealSftp import SftpOperate
    from dealFtp import FtpOperate
    from dealLocal import LocalOperate
    from oneMore import OneMore

"""
@author: hananmin
@time: 2018/12/27 9:28
@function:
    - 创建线程池
"""


class ThreadPoolObj(BaseObject):

    def __init__(self, logque, config_que, bak_dir):
        super(ThreadPoolObj, self).__init__()
        self.log_que = logque
        self.config_que = config_que
        self.bak_dir = bak_dir
        # self.log_entity = None

    def __deal_que_data(self, item):
        channel = item['channel']
        if 'sftp' in channel:
            sftp_operate = SftpOperate(self.log_que, item, self.bak_dir)
            sftp_operate.deal_sftp_config()
        elif 'ftp' in channel:
            ftp_operate=FtpOperate(self.log_que, item, self.bak_dir)
            ftp_operate.deal_ftp_config()
        elif channel == 'local':
            local_operate = LocalOperate(self.log_que, item,self.bak_dir)
            local_operate.deal_local_config()
        elif channel == 'one_more':
            onemore_operate = OneMore(self.log_que, item, self.bak_dir)
            onemore_operate.deal_one_more_config()

    def __get_que_data(self, ids):
        while True:
            if self.config_que.empty():
                break
            else:
                try:
                    item = self.config_que.get(block=False)
                    self.__deal_que_data(item)
                except Empty:
                    pass
                except:
                    traceback.print_exc()

    def pool(self):
        pool_ids = [x for x in range(5)]
        pool = threadpool.ThreadPool(5)
        pool_request = threadpool.makeRequests(self.__get_que_data, args_list=pool_ids)
        [pool.putRequest(req) for req in pool_request]
        pool.wait()

