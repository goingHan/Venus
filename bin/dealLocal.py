#!/usr/bin/env python
# encoding: utf-8
from bin.base import BaseObject
import glob
import os
import shutil
import stat
import traceback

"""
v1.0.1
@author: hananmin
@time: 2018/12/29 10:57
@function:
  - 处理本地流转
"""


class LocalOperate(BaseObject):

    def __init__(self, log_que, temp_config, bak_dir):
        super().__init__()
        self.temp_config = temp_config
        self.osn_dir = temp_config['from']
        self.file_pattern = temp_config['file']
        self.remote_dir = temp_config['to']
        self.bak_dir = bak_dir
        self.log_que = log_que
        self.log_entity = {
            'startSsh': '',
            'login': '',
            'kind': '',
            # 'statusCode': '',
            'status': True,
            'pattern': self.temp_config['file'],
            'ip': self.temp_config['ip'],
            'list': []
        }
        self.status = True
        self.status_code = '0000'

    def _set_code_status(self, state, code, message=''):
        self.status_code = code
        self.status = state
        if not state and self.log_entity['status']:
            self.log_entity['status'] = False
        if not state:
            return False, self.statusCode[code]+' '+message
        else:
            return True, self.statusCode[code]

    def __find_local_file(self):
        up_list = glob.glob(os.path.join(self.osn_dir, self.file_pattern))
        return up_list

    def __compare_local_size(self, osn_dir, filename):
        status = super()._compare_local_size(osn_dir, filename)
        if status:
            return self._set_code_status(True, '3005')
        else:
            return self._set_code_status(False, '3006', 'compare more than 10 times')

    def __bak_file(self, item, bak_dir):
        try:
            super()._bak_file(item, bak_dir)
            return self._set_code_status(True, '3013')
        except Exception as e:
            return self._set_code_status(False, '3014', str(e))

    def __move_file(self, item):
        try:
            local_local_file = item
            local_remote_file = os.path.join(self.remote_dir, os.path.basename(item))
            shutil.copy(local_local_file, local_remote_file)
            os.chmod(local_remote_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
            return self._set_code_status(True, '3007')
        except Exception as e:
            return self._set_code_status(False, '3008', str(e))

    def __rm_local_file(self, item):
        try:
            super()._rm_local_file(item)
            return self._set_code_status(True, '3011')
        except Exception as e:
            return self._set_code_status(False, '3012', str(e))

    def __combine_local(self, filename):
        all_filename = os.path.join(self.osn_dir, filename)
        com_code, com_message = self.__compare_local_size(self.osn_dir, filename)
        if not com_code:
            return self._inner_log_entity(compare=com_message)
        bak_code, bak_message = self.__bak_file(all_filename, self.bak_dir)
        if not bak_code:
            return self._inner_log_entity(compare=com_message, bak=bak_message)
        up_code, up_message = self.__move_file(filename)
        if not up_code:
            return self._inner_log_entity(compare=com_message, bak=bak_message, transport=up_message)
        rm_code, rm_messag = self.__rm_local_file(all_filename)
        return self._inner_log_entity(compare=com_message, bak=bak_message, transport=up_message,
                                      remove=rm_messag)

    def deal_local_config(self):
        # print(self.temp_config)
        channel = self.temp_config['channel']
        self.log_entity['kind'] = channel
        file_list = self.__find_local_file()
        for part in file_list:
            try:
                inner_log_entity = self.__combine_local(part)
            except Exception as e:
                _, other = self._set_code_status(False, '3015', str(e))
                inner_log_entity = self._inner_log_entity(other=other)
                traceback.print_exc()
            inner_log_entity['filename'] = part
            inner_log_entity['innerCode'] = self.status_code
            inner_log_entity['innerStatus'] = self.status
            self.log_entity['list'].append(inner_log_entity)
        else:
            _, other = self._set_code_status(True, '0002')
        self._add_queue(self.log_que, self.log_entity)

