#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/3/27 14:39
# @File    : aps_server.py
# @author  : dfkai
# @Software: PyCharm
"""
This is an example showing how to make the scheduler into a remotely accessible service.
It uses RPyC to set up a service through which the scheduler can be made to add, modify and remove
jobs.
To run, first install RPyC using pip. Then change the working directory to the ``rpc`` directory
and run it with ``python -m server``.
"""

import logging

import rpyc
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from rpyc.utils.server import ThreadedServer

logger = logging.getLogger('apscheduler')
logger.setLevel(logging.DEBUG)

logger_handler = logging.FileHandler('scheduler.log', mode='a', encoding='utf-8')
logger_handler.setLevel(logging.INFO)
logger_handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)s: %(message)s',
                                              datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(logger_handler)


class SchedulerService(rpyc.Service):
    def exposed_add_job(self, func, *args, **kwargs):
        return scheduler.add_job(func, *args, **kwargs)

    def exposed_modify_job(self, job_id, jobstore=None, **changes):
        return scheduler.modify_job(job_id, jobstore, **changes)

    def exposed_reschedule_job(self, job_id, jobstore=None, trigger=None, **trigger_args):
        return scheduler.reschedule_job(job_id, jobstore, trigger, **trigger_args)

    def exposed_pause_job(self, job_id, jobstore=None):
        return scheduler.pause_job(job_id, jobstore)

    def exposed_resume_job(self, job_id, jobstore=None):
        return scheduler.resume_job(job_id, jobstore)

    def exposed_remove_job(self, job_id, jobstore=None):
        scheduler.remove_job(job_id, jobstore)

    def exposed_get_job(self, job_id):
        return scheduler.get_job(job_id)

    def exposed_get_jobs(self, jobstore=None):
        return scheduler.get_jobs(jobstore)

    def exposed_print_jobs(self, jobstore=None):
        return scheduler.print_jobs(jobstore)



if __name__ == '__main__':
    """初始化"""
    jobstores = {
        # 'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')  # SQLAlchemyJobStore指定存储链接 # 由于pickle sqlalchemy 报错 只能取消存储
    }
    executors = {
        'default': {'type': 'threadpool', 'max_workers': 20},  # 最大工作线程数20
        'processpool': ProcessPoolExecutor(max_workers=5)  # 最大工作进程数为5
    }
    scheduler = BackgroundScheduler()
    scheduler.configure(jobstores=jobstores, executors=executors)
    scheduler.start()
    protocol_config = {'allow_public_attrs': True}
    server = ThreadedServer(SchedulerService, port=12345, protocol_config=protocol_config)
    try:
        print("start ")
        server.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown()
