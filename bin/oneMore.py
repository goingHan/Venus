#!/usr/bin/env python
# encoding: utf-8

try:
    from bin.base import MoreBase
except ModuleNotFoundError :
    from base import MoreBase
import os
import traceback
"""
@author: hananmin
@time: 2019/1/3 15:46
@function:
- 处理一处流转到多处
"""


class OneMore(MoreBase):

    def __init__(self, log_que, temp_config,bak_dir):
        super(OneMore, self).__init__()
        self.temp_config = temp_config
        self.log_que = log_que
        self.bak_dir = bak_dir

    def __sftp_down(self, filename):
        hsn_ok_list = {'filename': filename, 'list': []}
        hsn_err_list = {'filename': filename, 'list': []}
        compare_status, compare_code, compare_message = self._compare_remote_size(osn_dir=self.temp_config['from'],
                                                                  filename=filename)
        if not compare_status:
            hsn_err_list['list'].append({'code': compare_code, 'to': '*', 'message': compare_message})
            return compare_status, hsn_err_list, hsn_ok_list
        hsn_dirs = self.temp_config['to']
        all_true = True
        for part in hsn_dirs:
            down_status, code, down_message = self._down_file(file_name=filename,
                                                              hsn_dir=part, osn_dir=self.temp_config['from'])
            if not down_status:
                hsn_err_list['list'].append({'code': code, 'to': part, 'message': down_message})
                all_true = False
            else:
                hsn_ok_list['list'].append({'to': part})
        if not all_true:
            return all_true, hsn_err_list, hsn_ok_list
        rm_status, rm_code, rm_message = self._rm_remote_file(osn_dir=self.temp_config['from'], item=filename)
        if not rm_status:
            hsn_err_list[filename].append({'code': rm_code, 'to': '*', 'message': rm_message})
            return compare_status, hsn_err_list, hsn_ok_list
        return all_true, hsn_err_list, hsn_ok_list

    def __sftp_up(self, filename):
        hsn_ok_list = {'filename': filename, 'list': []}
        hsn_err_list = {'filename': filename, 'list': []}
        all_filename = os.path.join(self.temp_config['from'], filename)
        compare_status, compare_code, compare_message = self._compare_local_size(osn_dir=self.temp_config['from'],
                                                                                 filename=filename)
        if not compare_status:
            hsn_err_list['list'].append({'code': compare_code, 'to': '*', 'message': compare_message})
            return compare_status, hsn_err_list, hsn_ok_list
        bak_status, bak_code, bak_message = self._bak_file(item=all_filename, bak_dir=self.bak_dir)
        if not bak_status:
            hsn_err_list['list'].append({'code': bak_code, 'to': '*', 'message': bak_message})
            return compare_status, hsn_err_list, hsn_ok_list
        hsn_dirs = self.temp_config['to']
        all_true = True
        for part in hsn_dirs:
            up_status, code, up_message = self._upload_file(file_name=filename, hsn_dir=part)
            if not up_status:
                hsn_err_list['list'].append({'code': code, 'to': part, 'message': up_message})
                all_true = False
            else:
                hsn_ok_list['list'].append({'to': part})
        if not all_true:
            return all_true, hsn_err_list, hsn_ok_list
        rm_status, rm_code, rm_message = self._rm_local_file(item=filename)
        if not rm_status:
            hsn_err_list[filename].append({'code': rm_code, 'to': '*', 'message': rm_message})
            return compare_status, hsn_err_list, hsn_ok_list
        return all_true, hsn_err_list, hsn_ok_list

    def __local_move_file(self, filename):
        hsn_ok_list = {'filename': filename, 'list': []}
        hsn_err_list = {'filename': filename, 'list': []}
        all_filename = os.path.join(self.temp_config['from'], filename)
        compare_status, compare_code, compare_message = self._compare_local_size(osn_dir=self.temp_config['from'],
                                                                                 filename=filename)
        if not compare_status:
            hsn_err_list['list'].append({'code': compare_code, 'to': '*', 'message': compare_message})
            return compare_status, hsn_err_list, hsn_ok_list
        bak_status, bak_code, bak_message = self._bak_file(item=all_filename, bak_dir=self.bak_dir)
        if not bak_status:
            hsn_err_list['list'].append({'code': bak_code, 'to': '*', 'message': bak_message})
            return compare_status, hsn_err_list, hsn_ok_list
        hsn_dirs = self.temp_config['to']
        all_true = True
        for part in hsn_dirs:
            local_status, code, local_message = self._move_file(file_name=filename, hsn_dir=part)
            if not local_status:
                hsn_err_list['list'].append({'code': code, 'to': part, 'message': local_message})
                all_true = False
            else:
                hsn_ok_list['list'].append({'to': part})
        if not all_true:
            return all_true, hsn_err_list, hsn_ok_list
        rm_status, rm_code, rm_message = self._rm_local_file(item=filename)
        if not rm_status:
            hsn_err_list['list'].append({'code': rm_code, 'to': '*', 'message': rm_message})
            return compare_status, hsn_err_list, hsn_ok_list
        return all_true, hsn_err_list, hsn_ok_list

    def __handle_type(self):
        types = self.temp_config['type']
        if 'sftp' in types:
            ssh_status, ssh_code, ssh_message = self._open_sftp(ip_info=self.temp_config['ip'])
            if not ssh_status:
                return self._set_log_status(self.temp_config, ssh_status, ssh_code, ssh_message, self.log_que)
            login_status, login_code, login_message = self._sftp_login(user_name=self.temp_config['user'],
                                                                       password=self.temp_config['password'])
            if not login_status:
                return self._set_log_status(self.temp_config, login_status, login_code, login_message, self.log_que)
        if types == 'sftp_down':
            file_list = self._find_down_file(osn_dir=self.temp_config['from'],
                                             file_pattern=self.temp_config['file'])
            for part in file_list:
                try:
                    down_status,hsn_err_list, hsn_ok_list = self.__sftp_down(part)
                    if not down_status:
                        self.log_entity['statusCode'] = '0003'
                        self.log_entity['errList'].append(hsn_err_list)
                    else:
                        self.log_entity['okList'].append(hsn_ok_list)
                except Exception as e:
                    traceback.print_exc()
                    self.log_entity['errList'].append({part: [{'code': 3015, 'to': '*',
                                                               'message': str(e)}]})
            if not len(file_list):
                        return self._set_log_status(self.temp_config, True, '0002', '', self.log_que)
        if types == 'sftp_up':
            file_list = self._find_local_file(osn_dir=self.temp_config['from'],
                                             file_pattern=self.temp_config['file'])
            for part in file_list:
                try:
                    up_status, hsn_err_list, hsn_ok_list,  = self.__sftp_up(part)
                    if not up_status:
                        self.log_entity['statusCode'] = '0003'
                        self.log_entity['errList'].append(hsn_err_list)
                    else:
                        self.log_entity['okList'].append(hsn_ok_list)
                except Exception as e:
                    traceback.print_exc()
                    self.log_entity['errList'].append({part: [{'code': 3015, 'to': '*',
                                                               'message': str(e)}]})
            if not len(file_list):
                return self._set_log_status(self.temp_config, True, '0002', '', self.log_que)

        if types == 'local':
            file_list = self._find_local_file(osn_dir=self.temp_config['from'],
                                             file_pattern=self.temp_config['file'])
            for part in file_list:
                try:
                    up_status, hsn_err_list, hsn_ok_list = self.__local_move_file(part)
                    if not up_status:
                        self.log_entity['statusCode'] = '0003'
                        self.log_entity['errList'].append(hsn_err_list)
                    else:
                        self.log_entity['okList'].append(hsn_ok_list)
                except Exception as e:
                    traceback.print_exc()
                    self.log_entity['errList'].append({part: [{'code': 3015, 'to': '*',
                                                               'message': str(e)}]})
            if not len(file_list):
                        return self._set_log_status(self.temp_config, True, '0002', '', self.log_que)
        self._set_base_status(self.temp_config)
        self._add_queue(self.log_que, self.log_entity)

    def deal_one_more_config(self):
        try:
            self.__handle_type()
        finally:
            types = self.temp_config['type']
            if 'sftp' in types:
                self._close(self.sftp_objects, self.sftp_transport)

