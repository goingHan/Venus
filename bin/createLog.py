#!/usr/bin/env python
# encoding: utf-8
import logging
import traceback
try:
    from bin.base import BaseObject
except ModuleNotFoundError:
    from base import BaseObject
import datetime
import os

"""
@author: hananmin
@time: 2018/12/25 17:34
@function:
 -  把日志写入文件
"""


class LogGenerator(BaseObject):

    def __init__(self, log_que, event, logdir):
        self.log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(statusCode)s  "
                                            "%(statusInfo)s - %(message)s")
        super(LogGenerator,self).__init__()
        self.queue = log_que
        self.event = event
        self.up_logger = None
        self.down_logger = None
        self.local_logger = None
        self.start_time = datetime.datetime.now()
        self.count = 0
        self.logdir = logdir

    def __set_up_log(self):
        logger = logging.getLogger('UP')
        logger.setLevel(logging.INFO)
        log_name = os.path.join(self.logdir, 'up.log')
        fh = logging.FileHandler(log_name, mode='a+')
        fh.setLevel(logging.INFO)
        fh.setFormatter(self.log_format)
        logger.addHandler(fh)
        self.up_logger = logger

    def __set_down_log(self):
        logger = logging.getLogger('DOWN')
        logger.setLevel(logging.INFO)
        log_name = os.path.join(self.logdir, 'down.log')
        fh = logging.FileHandler(log_name, mode='a+')
        fh.setLevel(logging.INFO)
        fh.setFormatter(self.log_format)
        logger.addHandler(fh)
        self.down_logger = logger

    def __set_local_log(self):
        logger = logging.getLogger('LOCAL')
        logger.setLevel(logging.INFO)
        log_name = os.path.join(self.logdir, 'local.log')
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
        code = item['statusCode']
        status_info = self.statusCode[code]
        self.count = self.count + len(item['errList']) + len(item['okList'])
        if code in ['3001', '3004']:
            head_list = [item['kind'], ' ', item['pattern'], item['to'], item['ip'], '', '', item['error']]
            message = ','.join(head_list)
        else:
            head_list = [item['kind'], ' ',item['pattern'], item['to'], item['ip']]
            ok_list = item['okList']
            err_list = ['{0}-({1})'.format(part['filename'], self.statusCode[part['code']]+' '+part['message'])
                         for part in item['errList']]
            message = ','.join(head_list) + ',' + ' '.join(ok_list)+','+' '.join(err_list)
        if code in ['0000', '0002']:
            logger.info(message, extra={'statusCode': code,
                                         'statusInfo': status_info})
        else:
            logger.error(message, extra={'statusCode': code,
                                         'statusInfo': status_info})

    def __print_more_log(self, logger, item):
        code = item['statusCode']
        status_info = self.statusCode[code]
        err_nums = sum([len(part['list']) for part in item['okList']])
        ok_nums = sum([len(part['list']) for part in item['errList']])
        self.count = self.count + err_nums + ok_nums
        if code == '3001' or code == '3002':
            head_list = [item['kind'], item['type'], item['pattern'], item['ip'], '', '', item['error']]
            message = ','.join(head_list)
        else:
            head_list = [item['kind'], item['type'], item['pattern'], item['ip']]
            ok_list = []
            for part in item['okList']:
                file_name = part['filename']
                for part_other in part['list']:
                    ok_list.append('{0}-{1}'.format(file_name, part_other['to']))
            err_list = []
            for part in item['errList']:
                file_name = part['filename']
                for part_other in part['list']:
                    err_list.append('{0}-{1}-({2})'.format(file_name, part_other['to'],
                                                          self.statusCode[part_other['code']]+' '+part_other['message']))
            message = ' '.join(head_list) + ',' + ' '.join(ok_list)+','+' '.join(err_list)
        if code in ['0000', '0002']:
            logger.info(message, extra={'statusCode': code,
                                         'statusInfo': status_info})
        else:
            logger.error(message, extra={'statusCode': code,
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
            elif 'one_more' in kind:
                types = message['type']
                if 'up' in types:
                    self.__print_more_log(self.up_logger, message)
                elif 'down' in types:
                    self.__print_more_log(self.down_logger, message)
                elif 'local' in types:
                    self.__print_more_log(self.local_logger, message)
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
                # print(self.queue.qsize())
                item = self.queue.get(block=False)
                self.__generate_log(item)

