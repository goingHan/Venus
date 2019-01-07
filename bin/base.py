#!/usr/bin/env python
# encoding: utf-8

import time
import socket
import os
import shutil
import paramiko
from fnmatch import fnmatch
import glob
import stat

"""
@author: hananmin
@time: 2018/12/26 20:21
@function:
    - 基础类
"""


class BaseObject(object):

    def __init__(self):
        self.log_entity = {
            'kind': '',
            'type': '',
            'statusCode': '0000',
            'error': '',
            'pattern': '',
            'ip': '',
            'errList': [],
            'okList': []
        }
        self.statusCode = {
            '0000': 'SUCCESS',
            '0002': 'NO FILE',
            '0003':  'HAS ERROR',
            '3004': 'Login in failed',
            '3006': 'Compare failed',
            '3008': 'upload failed',
            '3010': 'download failed',
            '3012': 'remove failed',
            '3014': 'backup failed',
            '3015': 'unknow error',
            '3016': 'ftp connected failed',
            '3018': 'local file open failed',
            '3019': 'Part error',
        }

    def _set_base_status(self, temp_config):
        self.log_entity['kind'] = temp_config['channel']
        if 'type' in temp_config:
            self.log_entity['type'] = temp_config['type']
        self.log_entity['ip'] = temp_config['ip']
        self.log_entity['pattern'] = temp_config['file']
        self.log_entity['to'] = temp_config['to']

    def _set_log_status(self, temp_config, state, code, message, log_que):
        self._set_base_status(temp_config)
        self.log_entity['statusCode'] = code
        if not state:
            self.log_entity['error'] = message
        self._add_queue(log_que, self.log_entity)

    def _add_queue(self, que, item):
        que.put(item)

    def _get_queue(self, que):
        return que.get(block=False)

    def _get_time(self, sign):
        """获取时间

        1：'%Y%m%d %H:%M:%S,miel'
        0：'%Y%m%d'
        3：'%Y-%m-%d %H:%M:%S'
        other: timestamp
        """
        ct = time.time()
        msel = (ct - int(ct))*1000
        if sign == 1:
            prefix = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ct))
            return "{0},{1:.0f}".format(prefix, msel)
        elif sign == 0:
            return time.strftime('%Y%m%d', time.localtime(ct))
        elif sign == 3:
            return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ct))
        else:
            return int(ct)

    def __get_local_file_size(self, osn_dir, filename):
        osn_file_path = os.path.join(osn_dir, filename)
        file_size = os.path.getsize(osn_file_path)
        return file_size

    def _base_compare_local_size(self, osn_dir, filename):
        cycle = 0
        while True:
            ago_size = self.__get_local_file_size(osn_dir, filename)
            time.sleep(0.001)
            now_size = self.__get_local_file_size(osn_dir, filename)
            if ago_size == now_size:
                return True
            elif cycle == 10:
                return False
            cycle = cycle + 1

    def _rm_local_file(self, item):
        os.remove(item)

    def _base_bak_file(self, item, bak_dir):
        file_name = os.path.basename(item)
        all_bak_file = os.path.join(bak_dir, file_name)
        shutil.copy(item, all_bak_file)

    def __check_port(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        addr = (str(host), int(port))
        status = s.connect_ex(addr)
        if status != 0:
            return False
        else:
            return True

    def _get_port(self, item):
        i_p = item.split(':')
        host = i_p[0]
        if len(i_p) == 2:
            port = int(i_p[1])
        else:
            port = 22
        if self.__check_port(host, port):
            return True, host, port
        else:
            return False, None, None


# 装饰器
def decorator_fun(code):
    def inner_wrapper(funcs):
        def inner_fun(self, **arg):
            try:
                funcs(self, arg)
                return True, '0000', ''
            except Exception as e:
                return False, code, str(e)
        return inner_fun
    return inner_wrapper


class MoreBase(BaseObject):

    @decorator_fun(code='3001')
    def _open_sftp(self, arg):
        ip_info = arg['ip_info']
        port_status, ip, port = self._get_port(ip_info)
        if not port_status:
            raise Exception(ip_info)
        self.sftp_transport = paramiko.Transport((ip, port))
        # return '3002'

    @decorator_fun(code='3004')
    def _sftp_login(self, arg):
        user_name = arg['user_name']
        password = arg['password']
        self.sftp_transport.connect(username=user_name, password=password)
        self.sftp_objects = paramiko.SFTPClient.from_transport(self.sftp_transport)
        # return '3003'

    def _find_down_file(self, **arg):
        # print(self.osn_dir, self.file_pattern, self.temp_config)
        osn_dir = arg['osn_dir']
        file_pattern = arg['file_pattern']
        down_list = [down_part for down_part in self.sftp_objects.listdir(osn_dir)
                     if fnmatch(down_part, file_pattern)]
        return down_list

    def _find_local_file(self, osn_dir, file_pattern):
        up_list = glob.glob(os.path.join(osn_dir, file_pattern))
        return up_list

    def _get_remote_file_size(self, filename, osn_dir):
        # linux
        osn_file_path = os.path.join(osn_dir, filename)
        # osn_file_path = osn_dir+'/'+filename
        file_size = self.sftp_objects.lstat(osn_file_path).st_size
        return file_size

    @decorator_fun(code='3006')
    def _compare_remote_size(self, arg):
        filename = arg['filename']
        osn_dir = arg['osn_dir']
        cycle = 0
        while True:
            ago_size = self._get_remote_file_size(filename, osn_dir)
            time.sleep(0.001)
            now_size = self._get_remote_file_size(filename, osn_dir)
            if ago_size == now_size:
                return '3005'
            elif cycle == 10:
                raise Exception('compare more than 10 times')
            cycle = cycle + 1

    @decorator_fun(code='3006')
    def _compare_local_size(self, arg):
        osn_dir = arg['osn_dir']
        filename = arg['filename']
        status = super(MoreBase, self)._base_compare_local_size(osn_dir, filename)
        if status:
            pass
        else:
            raise Exception('compare more than 10 times')

    @decorator_fun(code='3014')
    def _bak_file(self, arg):
        item = arg['item']
        bak_dir = arg['bak_dir']
        super(MoreBase, self)._base_bak_file(item, bak_dir)
        # return '3013'

    @decorator_fun(code='3008')
    def _upload_file(self, arg):
        local_name = arg['file_name']
        remote_dir = arg['hsn_dir']
        # linux
        remote_name = os.path.join(remote_dir, os.path.basename(local_name))
        # remote_name = remote_dir + '/' + os.path.basename(local_name)
        self.sftp_objects.put(local_name, remote_name)
        # return '3007'

    @decorator_fun(code='3010')
    def _down_file(self, arg):
        file_name = arg['file_name']
        osn_dir = arg['osn_dir']
        hsn_dir = arg['hsn_dir']
        # linux
        remote_name = os.path.join(osn_dir, file_name)
        # remote_name = osn_dir + '/' + file_name
        local_name = os.path.join(hsn_dir, file_name)
        self.sftp_objects.get(remote_name, local_name)
        # return '3009'

    @decorator_fun(code='3012')
    def _rm_remote_file(self, arg):
        item = arg['item']
        osn_dir = arg['osn_dir']
        # linux
        file_name = os.path.join(osn_dir, item)
        # file_name = osn_dir + '/' +item
        self.sftp_objects.remove(file_name)
        # return '3011'

    @decorator_fun(code='3012')
    def _rm_local_file(self, arg):
        item = arg['item']
        super(MoreBase, self)._rm_local_file(item)
        # return '3011'

    def _close(self, sftp_objects, sftp_transport):
        sftp_objects.close()
        sftp_transport.close()

    @decorator_fun(code='3008')
    def _move_file(self, kwargs):
        remote_dir = kwargs['hsn_dir']
        item = kwargs['file_name']
        local_local_file = item
        local_remote_file = os.path.join(remote_dir, os.path.basename(item))
        shutil.copy(local_local_file, local_remote_file)
        os.chmod(local_remote_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        # return '3007'

