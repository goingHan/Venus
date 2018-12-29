#!/usr/bin/env python
# encoding: utf-8
import time
import socket
import os
import shutil

"""
v1.0.1
@author: hananmin
@time: 2018/12/26 20:21
@function:
    - 基础类
"""


class BaseObject:

    def __init__(self):
        self.statusCode = {
            '0000': '流转成功',
            '0001': '开始流转',
            '0002': '无文件流转',
            '3001': 'ssh connected failed',
            '3002': 'ssh connected successfully',
            '3003': 'Login in successfully',
            '3004': 'Login in failed',
            '3005': 'Compare successfully',
            '3006': 'Compare failed',
            '3007': 'upload successfully',
            '3008': 'upload failed',
            '3009': 'download successfully',
            '3010': 'download failed',
            '3011': 'remove successfully',
            '3012': 'remove failed',
            '3013': 'backup successfully',
            '3014': 'backup failed',
            '3015': 'unknow error',
            '3016': 'ftp connected failed',
            '3017': 'ftp connected successfully',
            '3018': 'local file open failed'
        }

    def _inner_log_entity(self, compare='', transport='', remove='', bak='', other='',
                          innerCode = '0000', innerStatus = ''):
        return {
            'compare': compare,
            'transport': transport,
            'remove': remove,
            'bak': bak,
            'filename': '',
            'other': other,
            'innerCode': innerCode,
            'innerStatus': innerStatus,
        }

    def _add_queue(self, que, item):
        que.put(item)

    def _get_queue(self, que):
        return que.get(block=False)

    def _get_time(self, sign):
        """获取时间

        1：'%Y%m%d %H:%M:%S,miel'
        0：'%Y%m%d'
        3：'%Y-%m-%d %H:%M:%S'
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

    def __get_local_file_size(self, osn_dir, filename):
        osn_file_path = os.path.join(osn_dir, filename)
        time.sleep(0.001)
        file_size = os.path.getsize(osn_file_path)
        return file_size

    def _compare_local_size(self, osn_dir, filename):
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

    def _bak_file(self, item, bak_dir):
        file_name = os.path.basename(item)
        all_bak_file = os.path.join(bak_dir, file_name)
        shutil.copy(item, all_bak_file)


class TcpBase(BaseObject):

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

