#!/usr/bin/env python
# encoding: utf-8
from bin.createLog import LogGenerator
from bin.config import ReadConfig
import multiprocessing

"""
v1.0.1
@author: hananmin
@time: 2018/12/25 17:34
@function:
 -  主函数
"""


class MainFunction:

    def __init__(self):
        # 日志队列
        self.log_que = multiprocessing.Queue()
        # 配置队列
        self.config_que = multiprocessing.Queue()
        #
        self.event = multiprocessing.Event()
        self.bak_dir = 'D:\Game\Config'

    def run(self):
        config_obj = ReadConfig(self.log_que, self.config_que, self.event, self.bak_dir)
        log_obj = LogGenerator(self.log_que, self.event)
        p1 = multiprocessing.Process(target=config_obj.run, args=())
        p2 = multiprocessing.Process(target=log_obj.read_queue, args=())
        p1.daemon = True
        p2.daemon = True
        p1.start()
        p2.start()
        p1.join()
        p2.join()


if __name__ == '__main__':
    main_obj = MainFunction()
    main_obj.run()

