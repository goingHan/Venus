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
@time: 2018/12/27 15:06
@function:
  -
   处理SFTP
"""


class SftpOperate(MoreBase):

    def __init__(self, log_que, temp_config,bak_dir):
        super(SftpOperate, self).__init__()
        self.temp_config = temp_config
        self.log_que = log_que
        self.bak_dir = bak_dir

    def __combine_down(self, filename):
        compare_status, compare_code, compare_message = self._compare_remote_size(
            osn_dir=self.temp_config['from'], filename=filename)
        if not compare_status:
            return compare_status, compare_code, compare_message
        down_status, down_code, down_message = self._down_file(file_name=filename, osn_dir=self.temp_config['from'],
                                                               hsn_dir=self.temp_config['to'])
        if not down_status:
            return down_status, down_code, down_message
        rm_status, rm_code, rm_message = self._rm_remote_file(item=filename,
                                                                        osn_dir=self.temp_config['from'])
        if not rm_status:
            return rm_status, rm_code, rm_message
        return True, None, None

    def __combine_up(self, filename):
        all_filename = os.path.join(self.temp_config['from'], filename)
        compare_status, compare_code, compare_message = self._compare_local_size(osn_dir=self.temp_config['from'],
                                                                                 filename=filename)
        if not compare_status:
            return compare_status, compare_code, compare_message
        bak_status, bak_code, bak_message = self._bak_file(item=all_filename, bak_dir=self.bak_dir)
        if not bak_status:
            return bak_status, bak_code, bak_message
        up_status, up_code, up_message = self._upload_file(file_name=filename, hsn_dir=self.temp_config['to'])
        if not up_status:
            return up_status, up_code, up_message
        rm_status, rm_code, rm_message = self._rm_local_file(item=all_filename)
        if not rm_status:
            return rm_status, rm_code, rm_message
        return True, None, None

    def deal_sftp_config(self):
        ssh_status, ssh_code, ssh_message = self._open_sftp(ip_info=self.temp_config['ip'])
        if not ssh_status:
            return self._set_log_status(self.temp_config, ssh_status, ssh_code, ssh_message, self.log_que)
        login_status, login_code, login_message = self._sftp_login(user_name=self.temp_config['user'],
                                                                   password=self.temp_config['password'])
        if not login_status:
            return self._set_log_status(self.temp_config, login_status, login_code, login_message, self.log_que)
        channel = self.temp_config['channel']
        try:
            if 'up' in channel:
                file_list = self._find_local_file(osn_dir=self.temp_config['from'],
                                                  file_pattern=self.temp_config['file'])
                for part in file_list:
                    try:
                        combine_status, combine_code, combine_message = self.__combine_up(part)
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
            if 'down' in channel:
                file_list = self._find_down_file(osn_dir=self.temp_config['from'],
                                                  file_pattern=self.temp_config['file'])
                for part in file_list:
                    try:
                        combine_status, combine_code, combine_message = self.__combine_down(part)
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
        finally:
            self._close(self.sftp_objects, self.sftp_transport)

