# -*- coding: utf-8 -*-
# @Time    : 2020/3/27 14:39
# @File    : rpc_client.py
# @author  : dfkai
# @Software: PyCharm
"""
This is an example RPC client that connects to the RPyC based scheduler service.
It first connects to the RPyC server on localhost:12345.
Then it schedules a job to run on 2 second intervals and sleeps for 10 seconds.
After that, it unschedules the job and exits.
"""

from time import sleep

import rpyc

conn = rpyc.connect('localhost', 12345)
job = conn.root.add_job('scheduler_script.test:print_text', 'interval', args=['Hello, World'], seconds=2)
sleep(10)
conn.root.remove_job(job.id)
