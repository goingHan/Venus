#!/usr/bin/env python
# encoding: utf-8
import logging
import traceback
from bin.base import BaseObject
import datetime

"""
v1.0.1
@author: hananmin
@time: 2018/12/25 17:34
@function:
 -  把日志写入文件
"""


class LogGenerator(BaseObject):

    def __init__(self, log_que, event):
        self.log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(statusCode)s  "
                                            "%(statusInfo)s - %(message)s")
        super().__init__()
        self.queue = log_que
        self.event = event
        self.up_logger = None
        self.down_logger = None
        self.local_logger = None
        self.start_time = datetime.datetime.now()
        self.count = 0

    def __set_up_log(self):
        logger = logging.getLogger('UP')
        logger.setLevel(logging.INFO)
        log_name = "../logs/up.log"
        fh = logging.FileHandler(log_name, mode='a+')
        fh.setLevel(logging.INFO)
        fh.setFormatter(self.log_format)
        logger.addHandler(fh)
        self.up_logger = logger

    def __set_down_log(self):
        logger = logging.getLogger('DOWN')
        logger.setLevel(logging.INFO)
        log_name = "../logs/down.log"
        fh = logging.FileHandler(log_name, mode='a+')
        fh.setLevel(logging.INFO)
        fh.setFormatter(self.log_format)
        logger.addHandler(fh)
        self.down_logger = logger

    def __set_local_log(self):
        logger = logging.getLogger('LOCAL')
        logger.setLevel(logging.INFO)
        log_name = "../logs/local.log"
        fh = logging.FileHandler(log_name, mode='a+')
        fh.setLevel(logging.INFO)
        fh.setFormatter(self.log_format)
        logger.addHandler(fh)
        self.local_logger = logger

    def setting(self):
        self.__set_up_log()
        self.__set_down_log()
        self.__set_local_log()
        # handler['sftp_up'] = up_logger
        # handler['sftp_down'] = down_logger
        # handler['local'] = local_logger
        # return handler

    def __print_log(self, logger, item):
        status = item['status']
        ip = item['ip']
        pattern = item['pattern']
        # status_info = self.statusCode[status_code]
        head_list = [item['kind'], pattern, ip, item['startSsh'], item['login'],
                     str(len(item['list']))]
        head_message = ','.join(head_list)
        logger.info(head_message, extra={'statusCode': '0001',
                                            'statusInfo': self.statusCode['0001']})
        self.count = self.count + len(item['list'])
        for part in item['list']:
            message_list = [part['filename'], part['compare'], part['bak'],
                           part['transport'], part['remove'], part['other']]
            message = ','.join(message_list)
            status_code = part['innerCode']
            status = part['innerStatus']
            status_info = self.statusCode[status_code]
            if status:
                logger.info(message, extra={'statusCode': status_code,
                                                               'statusInfo': status_info})
            else:
                logger.error(r"\033[91m"+message+r"\033[0m", extra={'statusCode': status_code,
                                                                'statusInfo': status_info})

    def __generate_log(self, message):
        """
        {
         'kind':"sftp_up/sftp_down/local",
         'status': True/False,
         'statusCode': "",
         'message': ""
        }
        :param message:
        :return:
        """
        try:
            kind = message['kind']
            if 'up' in kind:
                self.__print_log(self.up_logger, message)
            elif 'down' in kind:
                self.__print_log(self.down_logger, message)
            elif 'local' in kind:
                self.__print_log(self.local_logger, message)
        except:
            traceback.print_exc()

    def read_queue(self):
        self.setting()
        while True:
            if self.queue.empty():
                if self.event.is_set():
                    end = datetime.datetime.now()
                    all_second = end - self.start_time
                    print(self._get_time(3), all_second.total_seconds(), '---', self.count)
                    break
            else:
                item = self.queue.get(block=False)
                self.__generate_log(item)

