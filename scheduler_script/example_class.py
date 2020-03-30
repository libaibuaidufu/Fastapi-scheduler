#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/3/30 15:33
# @File    : example_class.py
# @author  : dfkai
# @Software: PyCharm
from datetime import datetime


class Hello:
    def main(self):
        print(datetime.now(), 'hello,world!')


def run():
    hello = Hello()
    hello.main()
