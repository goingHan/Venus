#!/usr/bin/env python
# encoding: utf-8
from ftplib import FTP
try:
    from bin.base import MoreBase, decorator_fun
except ImportError:
    from base import MoreBase, decorator_fun
from fnmatch import fnmatch
import os
import time
import traceback


"""
v1.0.1
@author: hananmin
@time: 2018/12/28 21:14
@function:
- 处理Ftp
"""


class FtpOperate(MoreBase):

    def __init__(self, log_que, temp_config, bak_dir):
        super(FtpOperate, self).__init__()
        self.temp_config = temp_config
        self.log_que = log_que
        self.bak_dir = bak_dir

    @decorator_fun(code='3016')
    def __open_ftp(self, kwargs):
        ip_info = kwargs['ip_info']
        self.ftp_objects = FTP(ip_info, timeout=2)

    @decorator_fun(code='3004')
    def _ftp_login(self, kwargs):
        user_name = kwargs['user_name']
        password = kwargs['password']
        self.ftp_objects.login(user=user_name, passwd=password)

    def __find_down_file(self, osn_dir, file_pattern):
        # print('---', self.ftp_objects.nlst(self.osn_dir))
        down_list = [down_part for down_part in self.ftp_objects.nlst(osn_dir)
                     if fnmatch(os.path.basename(down_part), file_pattern)]
        return down_list

    def __get_remote_file_size(self, filename):
        # linux
        # osn_file_path = os.path.join(self.osn_dir, filename)
        # osn_file_path = self.osn_dir+'/'+filename
        file_size = self.ftp_objects.size(filename)
        return file_size

    @decorator_fun(code='3006')
    def _compare_remote_size(self, kwargs):
        filename = kwargs['filename']
        cycle = 0
        while True:
            ago_size = self.__get_remote_file_size(filename)
            time.sleep(0.001)
            now_size = self.__get_remote_file_size(filename)
            if ago_size == now_size:
                return '3005'
            elif cycle == 10:
                raise Exception('compare more than 10 times')
            cycle = cycle + 1

    @decorator_fun(code='3008')
    def __ftp_upload_file(self, kwargs):
        file_name = kwargs['file_name']
        remote_dir = kwargs['osn_dir']
        local_name = file_name
        # linux
        remote_name = os.path.join(remote_dir, os.path.basename(file_name))
        # remote_name = remote_dir + '/' + os.path.basename(file_name)
        with open(local_name, 'rb') as ftp_local_objs:
            self.ftp_objects.storbinary('STOR %s' % remote_name, ftp_local_objs)

    @decorator_fun(code='3010')
    def __ftp_down_file(self, kwargs):
        file_name = kwargs['file_name']
        remote_dir = kwargs['hsn_dir']
        local_name = os.path.join(remote_dir, os.path.basename(file_name))
        with open(local_name, 'wb') as ftp_local_objs:
            self.ftp_objects.retrbinary('RETR %s' % file_name, ftp_local_objs.write)

    @decorator_fun(code='3012')
    def _ftp_rm_remote_file(self, kwargs):
        item = kwargs['item']
        self.ftp_objects.delete(item)

    def _ftp_close(self):
        self.ftp_objects.close()

    def __combine_down(self, filename):
        compare_status, compare_code, compare_message = self._compare_remote_size(
            osn_dir=self.temp_config['from'], filename=filename)
        if not compare_status:
            return compare_status, compare_code, compare_message
        down_status, down_code, down_message = self.__ftp_down_file(file_name=filename,hsn_dir=self.temp_config['to'])
        if not down_status:
            return down_status, down_code, down_message
        rm_status, rm_code, rm_message = self._ftp_rm_remote_file(item=filename)
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
        up_status, up_code, up_message = self.__ftp_upload_file(file_name=filename, osn_dir=self.temp_config['to'])
        if not up_status:
            return up_status, up_code, up_message
        rm_status, rm_code, rm_message = self._rm_local_file(item=all_filename)
        if not rm_status:
            return rm_status, rm_code, rm_message
        return True, None, None

    def deal_ftp_config(self):
        ftp_status, ftp_code, ftp_message = self.__open_ftp(ip_info=self.temp_config['ip'])
        if not ftp_status:
            return self._set_log_status(self.temp_config, ftp_status, ftp_code, ftp_message, self.log_que)
        login_status, login_code, login_message = self._ftp_login(user_name=self.temp_config['user'],
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
                file_list = self.__find_down_file(osn_dir=self.temp_config['from'],
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
            self._ftp_close()

