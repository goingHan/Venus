#!/usr/bin/env python
# encoding: utf-8

import pickle
import os
import time


"""
@author: hananmin
@time: 2019/1/3 10:43
@function:
- 处理序列化
- 处理增添标识
"""

BASE_PATH = os.path.abspath(__file__)
DB_FILE = os.path.join(os.path.dirname(BASE_PATH), '../db/venusdb') #'../db/venusdb'
KIND_LIST = ['sftp_up', 'sftp_down', 'local']
BASE_CODE = {
    '0001': 'already existed',
    '0002': 'remark or kind or dbkey can not be empty',
    '0003': 'dirs can not be empty',
    '0004': 'dbkey is not existed,must defined ahead',
    '0005': 'kind must is sftp_up or sftp_down or local',
    '0000': 'Success'
}


def get_timestamp():
    return int(time.time())


def log_output(code, message):
    if code == '0000':
        print('{0} : {1}'.format(BASE_CODE[code], message))
    else:
        err_message = '{0} : {1}'.format(BASE_CODE[code], message)
        print(r"\033[91m"+err_message+r"\033[0m")


def read_db():
    try:
        with open(DB_FILE, 'rb') as db:
            BASE_DATA = pickle.load(db)
    except FileNotFoundError:
        BASE_DATA = {}
    return BASE_DATA


def insert_db(kind, db_key, remark, path):
    BASE_DATA = read_db()
    if not db_key.strip() or not remark.strip() or not kind.strip():
        return '0002', ''
    if not kind in KIND_LIST:
        return '0005', ''
    if db_key in BASE_DATA:
        info = "type: {0} path: {1}".format(BASE_DATA[db_key]['kind'], ' '.join(BASE_DATA[db_key]['dirs']))
        return '0001', info
    if not len(path) > 0:
        return '0003', ''
    BASE_DATA[db_key] = {'remark': remark,
                         'date': get_timestamp(),
                         'kind': kind,
                         'dirs': path
                         }
    with open(DB_FILE, 'wb+') as db:
        pickle.dump(BASE_DATA, db, -1)
    return '0000', ''


def get_db_data(db_key):
    BASE_DATA = read_db()
    if not db_key.strip():
        return '0002', ''
    if not db_key in BASE_DATA:
        return '0004', ''
    return '0000', BASE_DATA


def look_db(db_key):
    code, BASE_DATA = get_db_data(db_key)
    if not code == '0000':
        return code, BASE_DATA
    remark = BASE_DATA[db_key]['remark']
    riqi = BASE_DATA[db_key]['date']
    dirs = ' '.join(BASE_DATA[db_key]['dirs'])
    kind = ' '.join(BASE_DATA[db_key]['kind'])
    info = "kind: {0} date: {1} remark: {2} \n  {3}".format(kind, riqi, remark, dirs)
    return '0000', info


def delete_db(db_key):
    code, BASE_DATA = get_db_data(db_key)
    if not code == '0000':
        return code, BASE_DATA
    BASE_DATA.pop(db_key)
    with open(DB_FILE, 'wb+') as db:
        pickle.dump(BASE_DATA, db, -1)
    return '0000', ''


def help_db():
    print("""
    insert kind  db_key remark path \n
              kind sftp_up/sftp_down/local \n
              db_key unique key,Define your own \n
              remark define your own \n
              path  absolute path,multiple files are separated by Spaces\n
    look   db_key \n
            db_key unique key,defined ahead \n
    delete db_key \n
            db_key unique key,defined ahead \n
    run   log_path \n
          log_path, The venus require the path where write the log   \n
    """)


#if __name__ == '__main__':
    #insert_db('sftp_up', 'sign_sftp_up', 'hananmin', '/app/ext4_test/01 /app/ext4_test/02 /app/ext4_test/03')

    #insert_db('sftp_down', 'sign_sftp_down', 'hananmin', r'D:\Game\002 D:\Game\003  D:\Game\004')
    #insert_db('local', 'sign_local', 'hananmin', r'D:\Game\002 D:\Game\003  D:\Game\004')
    #delete_db('sign_sftp_down')
#    _, info = look_db('sign_local')
#   print(info)
