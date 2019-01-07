#!/usr/bin/env python
# encoding: utf-8

try:
    from bin.base import MoreBase
except ModuleNotFoundError:
    from base import MoreBase
import os
import traceback

"""
@author: hananmin
@time: 2018/12/29 10:57
@function:
  - 处理本地流转
"""


class LocalOperate(MoreBase):

    def __init__(self, log_que, temp_config,bak_dir):
        super(LocalOperate, self).__init__()
        self.temp_config = temp_config
        self.log_que = log_que
        self.bak_dir = bak_dir

    def __combine_local(self, filename):
        all_filename = os.path.join(self.temp_config['from'], filename)
        compare_status, compare_code, compare_message = self._compare_local_size(osn_dir=self.temp_config['from'],
                                                                                filename=filename)
        if not compare_status:
            return compare_status, compare_code, compare_message
        bak_status, bak_code, bak_message = self._bak_file(item=all_filename, bak_dir=self.bak_dir)
        if not bak_status:
            return bak_status, bak_code, bak_message
        up_status, up_code, up_message = self._move_file(file_name=filename, hsn_dir=self.temp_config['to'])
        if not up_status:
            return up_status, up_code, up_message
        rm_status, rm_code, rm_message = self._rm_local_file(item=all_filename)
        if not rm_status:
            return rm_status, rm_code, rm_message
        return True, None, None

    def deal_local_config(self):
        file_list = self._find_local_file(osn_dir=self.temp_config['from'],
                                          file_pattern=self.temp_config['file'])
        for part in file_list:
            try:
                combine_status, combine_code, combine_message = self.__combine_local(part)
                if combine_status:
                    self.log_entity['okList'].append(part)
                else:
                    self.log_entity['statusCode'] = '0003'
                    self.log_entity['errList'].append({'filename': part, "code": combine_code,
                                                       'message': combine_message})
            except Exception as e:
                traceback.print_exc()
                self.log_entity['errList'].append({'filename': part, "code": '3015',
                                                   'message': str(e)})
        if not len(file_list):
            return self._set_log_status(self.temp_config, True, '0002', '', self.log_que)
        self._set_base_status(self.temp_config)
        self._add_queue(self.log_que, self.log_entity)


