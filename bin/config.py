#!/usr/bin/env python
# encoding: utf-8
from bin.base import BaseObject
from bin.threadPool import ThreadPoolObj
import traceback
import os

"""
v1.0.1
@author hananmin
function:
    - 加载配置文件
    - sftp_down 从远程下载文件到本地
    - sftp_up 从本地上传到远程
    - local 本地流转
    - deadIp 网络不通的IP
"""


class ReadConfig(BaseObject):

    def __init__(self, log_que, config_que, event, bak_dir):
        super().__init__()
        self.config_que = config_que
        self.event = event
        self.log_que = log_que
        self.config_dir = '../conf/'
        self.bak_dir = bak_dir

    def __look_list(self, list_obj):
        """
        - config_que
          配置信息的队列
        - channel
          流转方式：sftp_up/sftp_down/local
        - 队列内的单元
        {
        'channel': 'sftp_down/sftp_up/local',
        'from':'',
        'file':'',
        'to':'',
        'ip':'',
        'user':'',
        'password':''
        }
        :param list_obj:
        :return:
        """
        for part in list_obj:
           # self.config_que.put(part)
           self._add_queue(self.config_que, part)

    def __config_result(self, all_nums, error, ok):
        return 'read config end all:{0} error{1}  OK{2} '.format(all_nums,
                                                                 error, ok)

    def __end_read_config(self, err_nums, kind, config_list, all_nums):
        print(kind, self.__config_result(all_nums, err_nums, len(config_list)))
        if len(config_list) > 0:
            self.__look_list(config_list)

    def __exclude_annotations(self, entity, other=1):
        temp_entity = entity.strip().strip('\n')
        if temp_entity[0] == '#':
            return False, None
        else:
            if other == 1:
                return True, entity.strip().split(',')
            elif other == 0:
                return True, entity.strip().split()

    def __remove_n(self, list_obj):
        try:
            return list_obj.remove('\n')
        except ValueError:
            return list_obj
        except:
            traceback.print_exc()

    def __deal_up_config(self, kind):
        up_config_list = []
        err_nums = 0
        self.up_config = os.path.join(self.config_dir, kind)
        with open(self.up_config, 'r') as up_f_obj:
            up_lines = up_f_obj.readlines()
        up_lines = self.__remove_n(up_lines)
        if up_lines:
            for temp_part in up_lines:
                temp_status, part = self.__exclude_annotations(temp_part)
                if temp_status:
                    try:
                        temp = {
                            'channel': kind,
                            'from': part[0],
                            'to': part[5],
                            'ip': part[2],
                            'user': part[3],
                            'password': part[4],
                            'file': part[1],
                            }
                        up_config_list.append(temp)
                    except IndexError as index:
                        err_nums = err_nums+1
            self.__end_read_config(kind=kind, err_nums=err_nums, config_list=up_config_list,
                                   all_nums=len(up_lines))
        else:
            # self._add_log_queue(log_que=self.log_que, kind=kind, status_code='1009')
            print(kind, '未读取到配置文件')

    def __deal_down_config(self, kind):
        down_config_list = []
        err_nums = 0
        self.down_config = os.path.join(self.config_dir, kind)
        with open(self.down_config, 'r') as down_f_obj:
            down_lines = down_f_obj.readlines()
        down_lines = self.__remove_n(down_lines)
        if down_lines:
            for temp_part in down_lines:
                temp_status, part = self.__exclude_annotations(temp_part)
                if temp_status:
                    try:
                        temp = {
                            'channel': kind,
                            'from': part[3],
                            'to': part[5],
                            'ip': part[0],
                            'user': part[1],
                            'password': part[2],
                            'file': part[4],
                            }
                        down_config_list.append(temp)
                    except IndexError as index:
                        err_nums = err_nums+1
            self.__end_read_config(kind=kind, err_nums=err_nums, config_list=down_config_list,
                                   all_nums=len(down_lines))
        else:
            # self._add_log_queue(log_que=self.log_que, kind=kind, status_code='1009')
            print(kind, '未读取到配置文件')

    def __deal_local_config(self):
        kind = 'local'
        local_config_list = []
        err_nums = 0
        self.local_config = os.path.join(self.config_dir, kind)
        with open(self.local_config, 'r') as local_f_obj:
            local_lines = local_f_obj.readlines()
        local_lines = self.__remove_n(local_lines)
        if local_lines:
            for temp_part in local_lines:
                temp_status, part = self.__exclude_annotations(temp_part, other=0)
                if temp_status:
                    try:
                        temp = {
                            'channel': kind,
                            'from': part[0],
                            'to': part[4],
                            'ip': '',
                            'user': '',
                            'password': '',
                            'file': part[1],
                            }
                        local_config_list.append(temp)
                    except IndexError as index:
                        err_nums = err_nums+1
            self.__end_read_config(kind=kind, err_nums=err_nums, config_list=local_config_list,
                                   all_nums=len(local_lines))
        else:
            # self._add_log_queue(log_que=self.log_que, kind=kind, status_code='1009')
            print(kind, '未读取到配置文件')

    def __read_config(self):
        self.__deal_up_config('sftp_up')
        self.__deal_down_config('sftp_down')
        self.__deal_up_config('ftp_up')
        self.__deal_down_config('ftp_down')
        self.__deal_local_config()

    def run(self):
        self.__read_config()
        pool_obj = ThreadPoolObj(self.log_que, self.config_que, self.bak_dir)
        pool_obj.pool()
        self.event.set()

