#!/usr/bin/env python
# encoding: utf-8
try:
    from base import BaseObject
    from threadPool import ThreadPoolObj
    from sign import read_db
except ImportError: 
    from bin.base import BaseObject
    from bin.threadPool import ThreadPoolObj
    from bin.sign import read_db
import traceback
import os

"""
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
        super(ReadConfig, self).__init__()
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
        temp_entity = entity.strip()
        try:
            if not temp_entity:
                return False, None
            if temp_entity[0] == '#':
                return False, None
            else:
                if other == 1:
                    return True, entity.strip().split(',')
                elif other == 0:
                    return True, entity.strip().split()
        except:
            print('\033[1;35m'+'ERROR CONFIG'+'\033[0m', temp_entity, 'END')
            traceback.print_exc()
            return False, None

    def __remove_n(self, list_obj):
        try:
            list_obj.remove('\n')
            return list_obj
        except ValueError:
            return list_obj
        except:
            traceback.print_exc()
            return []

    def __deal_up_config(self, kind):
        up_config_list = []
        err_nums = 0
        self.up_config = os.path.join(self.config_dir, kind)
        with open(self.up_config, 'r') as up_f_obj:
            up_lines = up_f_obj.readlines()
        up_lines = self.__remove_n(up_lines)
        if up_lines or len(up_lines) == 0:
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
                    except IndexError:
                        err_nums = err_nums+1
            self.__end_read_config(kind=kind, err_nums=err_nums, config_list=up_config_list,
                                   all_nums=len(up_lines))
        else:
            # self._add_log_queue(log_que=self.log_que, kind=kind, status_code='1009')
            print(kind, 'The configuration file was not read')

    def __deal_down_config(self, kind):
        down_config_list = []
        err_nums = 0
        self.down_config = os.path.join(self.config_dir, kind)
        with open(self.down_config, 'r') as down_f_obj:
            down_lines = down_f_obj.readlines()
        down_lines = self.__remove_n(down_lines)
        if down_lines or len(down_lines) == 0:
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
                    except IndexError:
                        err_nums = err_nums+1
            self.__end_read_config(kind=kind, err_nums=err_nums, config_list=down_config_list,
                                   all_nums=len(down_lines))
        else:
            # self._add_log_queue(log_que=self.log_que, kind=kind, status_code='1009')
            print(kind, 'The configuration file was not read')

    def __deal_local_config(self):
        kind = 'local'
        local_config_list = []
        err_nums = 0
        self.local_config = os.path.join(self.config_dir, kind)
        with open(self.local_config, 'r') as local_f_obj:
            local_lines = local_f_obj.readlines()
        local_lines = self.__remove_n(local_lines)
        if local_lines or len(local_lines) == 0:
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
                    except IndexError:
                        err_nums = err_nums+1
            self.__end_read_config(kind=kind, err_nums=err_nums, config_list=local_config_list,
                                   all_nums=len(local_lines))
        else:
            # self._add_log_queue(log_que=self.log_que, kind=kind, status_code='1009')
            print(kind, 'The configuration file was not read')

    def __deal_one_more_config(self):
        kind = 'one_more'
        more_config_list = []
        err_nums = 0
        sign_data = read_db()
        self.more_config = os.path.join(self.config_dir, kind)
        with open(self.more_config, 'r') as more_f_obj:
            more_lines = more_f_obj.readlines()
            more_lines = self.__remove_n(more_lines)
        if more_lines or len(more_lines) == 0:
            for temp_part in more_lines:
                temp_status, part = self.__exclude_annotations(temp_part)
                if temp_status:
                    try:
                        temp = {
                            'channel': kind,
                            'type': part[0],
                            'from': part[1],
                            #'to': sign_data[part[6]]['dirs'].split(),
                            'to': sign_data[part[6]]['dirs'],
                            'ip': part[2],
                            'user': part[3],
                            'password': part[4],
                            'file': part[5],
                        }
                        more_config_list.append(temp)
                    except (IndexError,KeyError):
                        err_nums = err_nums + 1
                        print('one_more_exception: %s is not found' % part[6])
            self.__end_read_config(kind=kind, err_nums=err_nums, config_list=more_config_list,
                                   all_nums=len(more_lines))
        else:
            # self._add_log_queue(log_que=self.log_que, kind=kind, status_code='1009')
            print(kind, 'The configuration file was not read')

    def __read_config(self):
        self.__deal_up_config('sftp_up')
        self.__deal_down_config('sftp_down')
        self.__deal_up_config('ftp_up')
        self.__deal_down_config('ftp_down')
        self.__deal_local_config()
        self.__deal_one_more_config()

    def run(self):
        self.__read_config()
        pool_obj = ThreadPoolObj(self.log_que, self.config_que, self.bak_dir)
        pool_obj.pool()
        self.event.set()


