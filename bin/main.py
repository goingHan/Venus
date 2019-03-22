#!/usr/bin/env python
# encoding: utf-8
try:
    from bin.createLog import LogGenerator
    from bin.config import ReadConfig
    from bin.sign import help_db, insert_db, log_output, look_db, delete_db, look_all_db
except ImportError: 
    from createLog import LogGenerator
    from config import ReadConfig
    from sign import help_db, insert_db, log_output, look_db, delete_db, look_all_db
import multiprocessing
import sys
"""
@author: hananmin
@time: 2018/12/25 17:34
@function:
 -  主函数
"""


class MainFunction:

    def __init__(self, log_dir='../logs'):
        # 日志队列
        self.log_que = multiprocessing.Queue()
        # 配置队列
        self.config_que = multiprocessing.Queue()
        #
        self.event = multiprocessing.Event()
        self.bak_dir = '/NSFTP/bak'
        self.log_dir = log_dir

    def run(self):
        config_obj = ReadConfig(self.log_que, self.config_que, self.event, self.bak_dir)
        log_obj = LogGenerator(self.log_que, self.event, self.log_dir)
        p1 = multiprocessing.Process(target=config_obj.run, args=())
        p2 = multiprocessing.Process(target=log_obj.read_queue, args=())
        p1.daemon = True
        p2.daemon = True
        p1.start()
        p2.start()
        p1.join()
        p2.join()

    def handle_sign(self, way, args):
        if way == 'insert':
            try:
                kind = args[0]
                db_key = args[1]
                remark = args[2]
                path_list = args[3:]
                code, message = insert_db(kind, db_key, remark, path_list)
                log_output(code, message)
            except Exception:
                help_db()
        elif way == 'look':
            try:
                db_key = args[0]
                code, message = look_db(db_key)
                log_output(code, message)
            except Exception:
                help_db()
        elif way == 'lookAll':
            look_all_db()
        elif way == 'delete':
            try:
                db_key = args[0]
                code, message = delete_db(db_key)
                log_output(code, message)
            except Exception:
                help_db()
        elif way == 'run':
            if len(args) > 0:
                log_dir = args[0]
                self.log_dir = log_dir
            self.run()
        else:
            help_db()


if __name__ == '__main__':
    main_obj = MainFunction()
    arg_num = len(sys.argv)
    if arg_num > 1:
        way = sys.argv[1]
        other_argv = sys.argv[2:]
        main_obj.handle_sign(way, other_argv)
    else:
        help_db()


