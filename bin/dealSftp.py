#!/usr/bin/env python
# encoding: utf-8

import paramiko
from bin.base import TcpBase
from fnmatch import fnmatch
import glob
import os
import time
import traceback

"""
v1.0.1
@author: hananmin
@time: 2018/12/27 15:06
@function:
  -
   处理SFTP
"""


class SftpBase(TcpBase):
    def __init__(self):
       super().__init__()


class SftpOperate(SftpBase):

    def __init__(self, log_que, temp_config, bak_dir):
        super().__init__()
        self.temp_config = temp_config
        self.osn_dir = temp_config['from']
        self.file_pattern = temp_config['file']
        self.remote_dir = temp_config['to']
        self.bak_dir = bak_dir
        self.log_que = log_que
        self.sftp_objects = None
        self.sftp_transport = None
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

    def __open_sftp(self):
        item = self.temp_config['ip']
        port_status, ip, port = self._get_port(item)
        if not port_status:
            return self._set_code_status(port_status, '3001')
        try:
            self.sftp_transport = paramiko.Transport((ip, port))
            return self._set_code_status(True, '3002')
        except Exception as e:
            return self._set_code_status(False, '3001', str(e))

    def __sftp_login(self):
        user_name = self.temp_config['user']
        password = self.temp_config['password']
        try:
            self.sftp_transport.connect(username=user_name, password=password)
            self.sftp_objects = paramiko.SFTPClient.from_transport(self.sftp_transport)
            return self._set_code_status(True, '3003')
        except Exception as e:
            return self._set_code_status(False, '3004', str(e))

    def _find_down_file(self):
        # print(self.osn_dir, self.file_pattern, self.temp_config)
        down_list = [down_part for down_part in self.sftp_objects.listdir(self.osn_dir)
                     if fnmatch(down_part, self.file_pattern)]
        return down_list

    def __find_local_file(self):
        up_list = glob.glob(os.path.join(self.osn_dir, self.file_pattern))
        return up_list

    def __get_remote_file_size(self, filename):
        # linux
        osn_file_path = os.path.join(self.osn_dir, filename)
        # osn_file_path = self.osn_dir+'/'+filename
        file_size = self.sftp_objects.lstat(osn_file_path).st_size
        return file_size

    def __compare_remote_size(self, filename):
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

    def __upload_file(self, file_name):
        local_name = file_name
        # linux
        remote_name = os.path.join(self.remote_dir, os.path.basename(file_name))
        # remote_name = self.remote_dir + '/' + os.path.basename(file_name)
        try:
            self.sftp_objects.put(local_name, remote_name)
            return self._set_code_status(True, '3007')
        except Exception as e:
            return self._set_code_status(False, '3008', str(e))

    def __down_file(self, file_name):
        remote_name = os.path.join(self.osn_dir, file_name)
        local_name = os.path.join(self.remote_dir, file_name)
        try:
            self.sftp_objects.get(remote_name, local_name)
            return self._set_code_status(True, '3009')
        except Exception as e:
            return self._set_code_status(False, '3009', str(e))

    def __rm_remote_file(self, item):
        try:
            # linux
            file_name = os.path.join(self.osn_dir, item)
            # file_name = self.osn_dir + '/' +item
            self.sftp_objects.remove(file_name)
            return self._set_code_status(True, '3011')
        except Exception as e:
            return self._set_code_status(False, '3012', str(e))

    def __rm_local_file(self, item):
        try:
            super()._rm_local_file(item)
            return self._set_code_status(True, '3011')
        except Exception as e:
            return self._set_code_status(False, '3012', str(e))

    def __close(self):
        self.sftp_objects.close()
        self.sftp_transport.close()

    def __combine_down(self, filename):
        com_code, com_message = self.__compare_remote_size(filename)
        if not com_code:
            return self._inner_log_entity(compare=com_message)
        down_code, down_message = self.__down_file(filename)
        if not down_code:
            return self._inner_log_entity(compare=com_message, transport=down_message)
        _, rm_message = self.__rm_remote_file(filename)
        return self._inner_log_entity(compare=com_message, transport=down_message,
                                          remove=rm_message)

    def __combine_up(self, filename):
        all_filename = os.path.join(self.osn_dir, filename)
        com_code, com_message = self.__compare_local_size(self.osn_dir, filename)
        if not com_code:
            return self._inner_log_entity(compare=com_message)
        bak_code, bak_message = self.__bak_file(all_filename, self.bak_dir)
        if not bak_code:
            return self._inner_log_entity(compare=com_message, bak=bak_message)
        up_code, up_message = self.__upload_file(filename)
        if not up_code:
            return self._inner_log_entity(compare=com_message, bak=bak_message, transport=up_message)
        rm_code, rm_messag = self.__rm_local_file(all_filename)
        return self._inner_log_entity(compare=com_message, bak=bak_message, transport=up_message,
                                      remove=rm_messag)

    def deal_sftp_config(self):
        channel = self.temp_config['channel']
        open_code, self.log_entity['startSsh'] = self.__open_sftp()
        self.log_entity['kind'] = channel
        if not open_code:
            self._add_queue(self.log_que, self.log_entity)
            return
        login_code, self.log_entity['login'] = self.__sftp_login()
        if not login_code:
            self._add_queue(self.log_que, self.log_entity)
            return
        try:
            if 'up' in channel:
                file_list = self.__find_local_file()
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
            self.__close()

