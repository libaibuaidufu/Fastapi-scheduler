#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/3/25 11:24
# @File    : main.py
# @author  : dfkai
# @Software: PyCharm
import os
import time
from datetime import datetime
from typing import List

import rpyc
import uvicorn as u
from databases import Database, DatabaseURL
from fastapi import FastAPI, UploadFile, File
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from TreeNode import TreeNode
from aps_server import logger

scheduler_script_path = 'scheduler_script'
script_path = os.path.join(os.getcwd(), scheduler_script_path)
app = FastAPI()
dburl = DatabaseURL(f'mysql+pymysql://root:password@localhost:3306/dbname')
database = Database(dburl)

app.mount("/static", StaticFiles(directory="static"), name="static")

# 创建一个templates（模板）对象，以后可以重用。
templates = Jinja2Templates(directory="templates")


class JobId(BaseModel):
    id: str = None


class UpdateJob(BaseModel):
    id: str = None
    script_name: str = None
    schedule_name: str = None
    schedule_desc: str = None
    cron_second: str = None
    cron_minutes: str = None
    cron_hour: str = None
    cron_day_of_month: str = None
    cron_day_of_week: str = None
    cron_month: str = None


class AddJob(BaseModel):
    script_name: str = None
    schedule_name: str = None
    schedule_desc: str = None
    cron_second: str = None
    cron_minutes: str = None
    cron_hour: str = None
    cron_day_of_month: str = None
    cron_day_of_week: str = None
    cron_month: str = None


conn = None
bgsrv = None
scheduler = None


@app.on_event('startup')
async def startup():
    global conn, bgsrv, scheduler

    try:
        conn = rpyc.connect("localhost", 12345)
        # create a bg thread to process incoming events
        bgsrv = rpyc.BgServingThread(conn)
        scheduler = conn.root
    except ConnectionRefusedError as e:
        logger.error("请先执行 aps_server.py,否则无法使用web")
        raise
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    conn.close()
    await database.disconnect()


@app.get("/")
async def read_item(request: Request):
    # 获取数据库中job
    results = await database.fetch_all(
        "select id,schedule_name,schedule_desc,is_lock,priority,cron_second,cron_minutes,cron_hour,cron_day_of_month,cron_day_of_week,cron_month,enabled,run_type,script_name from scheduler ")
    job_results: List[dict] = []
    for result in results:
        task_plan = ' '.join(result[5:11])
        job_dict = dict(
            id=result[0],
            schedule_name=result[1],
            schedule_desc=result[2],
            is_lock=result[3],
            priority=result[4],
            cron_second=result[5],
            cron_minutes=result[6],
            cron_hour=result[7],
            cron_day_of_month=result[8],
            cron_day_of_week=result[9],
            cron_month=result[10],
            enabled=result[11],
            run_type=result[12],
            script_name=result[13],
            task_plan=task_plan,
        )
        job_results.append(job_dict)

    # 获取运行中的job
    jobs = scheduler.get_jobs()
    data = []
    for i in jobs:
        cron_info_dict = dict()
        cron_info_val = []
        cron_info_name = []
        next_run_time = ""
        if hasattr(i, 'next_run_time'):
            next_run_time = str(i.next_run_time.strftime("%Y-%m-%d %H:%M:%S")) if i.next_run_time else ""
        if hasattr(i.trigger, 'fields'):
            for value in i.trigger.fields:
                cron_info_dict[str(value.name)] = str(value)
                cron_info_val.append(str(value))
                cron_info_name.append(str(value.name))
        cron_info_val.reverse()
        cron_info = " ".join(cron_info_val)
        data.append({
            'id': i.id,
            'name': i.name,
            'pending': i.pending + 0,
            'cron_info_dict': cron_info_dict,
            'cron_info': cron_info,
            'next_run_time': next_run_time,
            'func_ref': i.func_ref,
        })

    # 获取脚本文件
    tree_node = TreeNode('脚本文件')
    script_name_list = [tree_node.get_node(script_path).get_name()]
    return templates.TemplateResponse("index.html", {"request": request, 'run_jobs': data, 'job_results': job_results,
                                                     'script_name_list': script_name_list})


@app.get("/print_jobs/")
async def print_jobs():
    scheduler.print_jobs()
    return {"reslut": "succ"}


@app.get("/close_aps/")
async def close_aps():
    scheduler.shutdown()


@app.get('/start_aps/')
async def start_aps():
    scheduler.start(paused=True)


@app.post("/add_job/")
async def add_job(job: JobId):
    # 添加调度任务
    job_sql = f'select schedule_name,cron_second,cron_minutes,cron_hour,cron_day_of_month,cron_day_of_week,cron_month,script_name from scheduler where id={job.id}'
    result = await database.fetch_one(job_sql)
    job_id = f'{job.id}_{int(time.time())}'
    try:
        scheduler.add_job(result[7],
                          trigger='cron',
                          id=job_id,
                          name=result[0],
                          misfire_grace_time=60 * 60,
                          coalesce=True,
                          max_instances=999,
                          second=result[1],
                          minute=result[2],
                          hour=result[3],
                          day=result[4],
                          day_of_week=result[5],
                          month=result[6],
                          )
        return {'result': 'succ'}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="id not found")


@app.post("/reschedule_job/")
async def reschedule_job(job: UpdateJob):
    try:
        scheduler.reschedule_job(
            job_id=job.id,
            trigger='cron',
            second=job.cron_second,
            minute=job.cron_minutes,
            hour=job.cron_hour,
            day=job.cron_day_of_month,
            day_of_week=job.cron_day_of_week,
            month=job.cron_month
        )
        return {'result': 'succ'}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="id not found")


@app.post("/remove_job/")
async def remove_job(job: JobId):
    try:
        scheduler.remove_job(job_id=job.id)
        return {'result': 'succ'}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="id not found")


@app.post('/modify_job/')
async def modify_job(job: JobId):
    try:
        scheduler.modify_job(job_id=job.id)
        return {'result': 'succ'}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="id not found")


@app.post("/pause_job/")
async def pause_job(job: JobId):
    try:
        scheduler.pause_job(job.id)
        return {'result': 'succ'}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="id not found")


@app.post("/resume_job/")
async def resume_job(job: JobId):
    try:
        scheduler.resume_job(job.id)
        return {'result': 'succ'}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="id not found")


@app.post("/update_db_job/")
async def update_db_job(job: UpdateJob):
    update_sql = f"update  scheduler set schedule_name='{job.schedule_name}' ,schedule_desc='{job.schedule_desc}',cron_second='{job.cron_second}',cron_minutes='{job.cron_minutes}',cron_hour='{job.cron_hour}',cron_day_of_month='{job.cron_day_of_month}',cron_day_of_week='{job.cron_day_of_week}',cron_month='{job.cron_month}',script_name='{job.script_name}'  where id={job.id}"
    await database.execute(update_sql)
    return {'result': 'succ'}


@app.post('/add_db_job/')
async def add_db_job(job: AddJob):
    now = datetime.now()
    insert_sql = "insert into   scheduler(script_name,schedule_name,schedule_desc,cron_second,cron_minutes,cron_hour,cron_day_of_month,cron_day_of_week,cron_month,create_time,priority,enabled,run_type,is_lock) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % (
        job.script_name, job.schedule_name, job.schedule_desc, job.cron_second, job.cron_minutes, job.cron_hour,
        job.cron_day_of_month, job.cron_day_of_week, job.cron_month, now, 999, 0, 1, 1)
    await database.execute(insert_sql)
    return {'result': 'succ'}


@app.post('/delete_db_job/')
async def delete_db_job(job: UpdateJob):
    update_sql = f"delete from  scheduler where id={job.id}"
    await database.execute(update_sql)
    return {'result': 'succ'}


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(script_path, file.filename)
        if os.path.exists(file_path):
            return {'result': 'fail', 'msg': '文件名重复'}
        with open(file_path, 'wb') as f:
            f.write(file.file.read())
        return {"filename": file.filename, 'result': 'succ'}
    except Exception as e:
        raise HTTPException(status_code=400, detail="file upload fail")


@app.get('/list_file/')
async def list_file():
    def has_py(file: str) -> bool:
        if file.endswith('.py') and not file.startswith('__'):
            return True
        return False

    data = list(filter(has_py, os.listdir(script_path)))
    script_path_list = []
    for index, i in enumerate(data):
        script_path_list.append(
            {"value": index + 1, "title": i, "disabled": "", "checked": ""}

        )
    return {'data': script_path_list}


if __name__ == '__main__':
    u.run(app, host="0.0.0.0", port=8081)
