#!/usr/bin/env python
# encoding: utf-8
from ftplib import FTP
from bin.base import TcpBase
from fnmatch import fnmatch
import glob
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


class FtpOperate(TcpBase):
    def __init__(self, log_que, temp_config, bak_dir):
        super().__init__()
        self.temp_config = temp_config
        self.osn_dir = temp_config['from']
        self.file_pattern = temp_config['file']
        self.remote_dir = temp_config['to']
        self.bak_dir = bak_dir
        self.log_que = log_que
        self.ftp_objects = None
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

    def __open_ftp(self):
        item = self.temp_config['ip']
        try:
            self.ftp_objects = FTP(item, timeout=2)
            return self._set_code_status(True, '3017')
        except Exception as e:
            return self._set_code_status(False, '3016', str(e))

    def __ftp_login(self):
        user_name = self.temp_config['user']
        password = self.temp_config['password']
        try:
            self.ftp_objects.login(user=user_name, passwd=password)
            return self._set_code_status(True, '3003')
        except Exception as e:
            return self._set_code_status(False, '3004', str(e))

    def _find_down_file(self):
        # print('---', self.ftp_objects.nlst(self.osn_dir))
        down_list = [down_part for down_part in self.ftp_objects.nlst(self.osn_dir)
                     if fnmatch(os.path.basename(down_part), self.file_pattern)]
        return down_list

    def _find_local_file(self):
        up_list = glob.glob(os.path.join(self.osn_dir, self.file_pattern))
        return up_list

    def __get_remote_file_size(self, filename):
        # linux
        # osn_file_path = os.path.join(self.osn_dir, filename)
        # osn_file_path = self.osn_dir+'/'+filename
        file_size = self.ftp_objects.size(filename)
        return file_size

    def _compare_remote_size(self, filename):
        cycle = 0
        while True:
            ago_size = self.__get_remote_file_size(filename)
            time.sleep(0.001)
            now_size = self.__get_remote_file_size(filename)
            if ago_size == now_size:
                return self._set_code_status(True, '3005')
            elif cycle == 10:
                return self._set_code_status(False, '3006', 'compare more than 10 times')
            cycle = cycle + 1

    def _compare_local_size(self, osn_dir, filename):
        status = super()._compare_local_size(osn_dir, filename)
        if status:
            return self._set_code_status(True, '3005')
        else:
            return self._set_code_status(False, '3006', 'compare more than 10 times')

    def _bak_file(self, item, bak_dir):
        try:
            super()._bak_file(item, bak_dir)
            return self._set_code_status(True, '3013')
        except Exception as e:
            return self._set_code_status(False, '3014', str(e))

    def __upload_file(self, file_name):
        local_name = file_name
        # linux
        remote_name = os.path.join(self.remote_dir, os.path.basename(file_name))
        # remote_name = self.remote_dir + '/' + os.path.basename(file_name)
        try:
            ftp_local_objs = open(local_name, 'rb')
        except Exception as e:
            return self._set_code_status(True, '3018', str(e))
        try:
            self.ftp_objects.storbinary('STOR %s' % remote_name, ftp_local_objs)
            return self._set_code_status(True, '3007')
        except Exception as e:
            return self._set_code_status(False, '3008', str(e))
        finally:
            ftp_local_objs.close()

    def __down_file(self, file_name):
        remote_name = file_name
        local_name = os.path.join(self.remote_dir, os.path.basename(file_name))
        try:
            ftp_local_objs = open(local_name, 'wb')
        except Exception as e:
            return self._set_code_status(False, '3018', str(e))
        try:
            self.ftp_objects.retrbinary('RETR %s' % remote_name, ftp_local_objs.write)
            return self._set_code_status(True, '3009')
        except Exception as e:
            return self._set_code_status(False, '3009', str(e))
        finally:
            ftp_local_objs.close()

    def _rm_remote_file(self, item):
        try:
            #linux
            # file_name = os.path.join(self.osn_dir, item)
            # file_name = self.osn_dir + '/' +item
            self.ftp_objects.delete(item)
            return self._set_code_status(True, '3011')
        except Exception as e:
            return self._set_code_status(False, '3012', str(e))

    def _rm_local_file(self, item):
        try:
            super()._rm_local_file(item)
            return self._set_code_status(True, '3011')
        except Exception as e:
            return self._set_code_status(False, '3012', str(e))

    def _close(self):
        self.ftp_objects.close()

    def __combine_down(self, filename):
        com_code, com_message = self._compare_remote_size(filename)
        if not com_code:
            return self._inner_log_entity(compare=com_message)
        down_code, down_message = self.__down_file(filename)
        if not down_code:
            return self._inner_log_entity(compare=com_message, transport=down_message)
        _, rm_message = self._rm_remote_file(filename)
        return self._inner_log_entity(compare=com_message, transport=down_message,
                                          remove=rm_message)

    def __combine_up(self, filename):
        all_filename = os.path.join(self.osn_dir, filename)
        com_code, com_message = self._compare_local_size(self.osn_dir, filename)
        if not com_code:
            return self._inner_log_entity(compare=com_message)
        bak_code, bak_message = self._bak_file(all_filename, self.bak_dir)
        if not bak_code:
            return self._inner_log_entity(compare=com_message, bak=bak_message)
        up_code, up_message = self.__upload_file(filename)
        if not up_code:
            return self._inner_log_entity(compare=com_message, bak=bak_message, transport=up_message)
        rm_code, rm_messag = self._rm_local_file(all_filename)
        return self._inner_log_entity(compare=com_message, bak=bak_message, transport=up_message,
                                      remove=rm_messag)

    def deal_ftp_config(self):
        channel = self.temp_config['channel']
        open_code, self.log_entity['startSsh'] = self.__open_ftp()
        self.log_entity['kind'] = channel
        if not open_code:
            self._add_queue(self.log_que, self.log_entity)
            return
        login_code, self.log_entity['login'] = self.__ftp_login()
        if not login_code:
            self._add_queue(self.log_que, self.log_entity)
            return
        try:
            if 'up' in channel:
                file_list = self._find_local_file()
                for part in file_list:
                    try:
                        inner_log_entity = self.__combine_up(part)
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
            else:
                file_list = self._find_down_file()
                for part in file_list:
                    try:
                        inner_log_entity = self.__combine_down(part)
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
        finally:
            self._close()

