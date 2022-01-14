# -*- coding: utf-8 -*-
# @Time    : 2020/3/25 11:24
# @File    : main_rpc_server.py
# @author  : dfkai
# @Software: PyCharm
import os
import time
from datetime import datetime
from typing import List

import rpyc
import sqlalchemy
import uvicorn as u
from databases import Database, DatabaseURL
from fastapi import FastAPI, UploadFile, File
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from TreeNode import TreeNode
from config import DATABASE_URL
from rpc_server.rpc_server import logger

scheduler_script_name = 'rpc_server/scheduler_script'

script_path = os.path.join(os.getcwd(), scheduler_script_name)
if not os.path.exists(script_path):
    os.mkdir(script_path)

app = FastAPI()
dburl = DatabaseURL(DATABASE_URL)
database = Database(dburl)

app.mount("/static", StaticFiles(directory="static"), name="static")

# 创建一个templates（模板）对象，以后可以重用。
templates = Jinja2Templates(directory="templates")

# 下面是使用sqlalchemy连接
metadata = sqlalchemy.MetaData()

sche = sqlalchemy.Table(
    "scheduler",
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),  # int
    sqlalchemy.Column('script_name', sqlalchemy.String(100), nullable=False, comment='脚本位置'),  # varchar
    sqlalchemy.Column('schedule_name', sqlalchemy.String(50), comment='定时任务名称'),  # varchar
    sqlalchemy.Column('schedule_desc', sqlalchemy.String(255), comment='定时任务描述'),  # varchar
    sqlalchemy.Column('cron_second', sqlalchemy.String(20), default='*', comment='定时任务-秒'),  # varchar
    sqlalchemy.Column('cron_minutes', sqlalchemy.String(20), default='*', comment='定时任务-分'),  # varchar
    sqlalchemy.Column('cron_hour', sqlalchemy.String(20), default='*', comment='定时任务-时'),  # varchar
    sqlalchemy.Column('cron_day_of_month', sqlalchemy.String(50), default='*', comment='定时任务-每月几号'),  # varchar
    sqlalchemy.Column('cron_day_of_week', sqlalchemy.String(50), default='*', comment='定时任务-每周星期几'),  # varchar
    sqlalchemy.Column('cron_month', sqlalchemy.String(20), default='*', comment='定时任务-月'),  # varchar
    sqlalchemy.Column('run_type', sqlalchemy.String(1), comment='运行类型 1 启动'),  # varchar
    sqlalchemy.Column('enabled', sqlalchemy.SmallInteger, comment=''),  # int
    sqlalchemy.Column('is_lock', sqlalchemy.SmallInteger, comment=''),  # int
    sqlalchemy.Column('priority', sqlalchemy.SmallInteger, comment=''),  # int
    sqlalchemy.Column('create_time', sqlalchemy.DateTime, default=datetime.now),  # datetime
)

engine = sqlalchemy.create_engine(
    DATABASE_URL
)
metadata.create_all(engine)
conn = None
bgsrv = None
scheduler = None


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


@app.on_event('startup')
async def startup():
    global conn, bgsrv, scheduler

    try:
        conn = rpyc.connect("localhost", 12345)
        # create a bg thread to process incoming events
        bgsrv = rpyc.BgServingThread(conn)
        scheduler = conn.root
    except ConnectionRefusedError as e:
        logger.error("请先执行 rpc_server.py,否则无法使用web")
        raise
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    conn.close()
    await database.disconnect()


@app.get("/")
async def index(request: Request):
    # 获取数据库中job
    query = sche.select().reduce_columns([sche.c.id])
    job_db_results = await database.fetch_all(query)
    job_results: List[dict] = []

    for table_i in job_db_results:
        table_i = dict(table_i)
        table_i['create_time'] = str(table_i['create_time'])
        table_i['task_plan'] = ' '.join(list(table_i.values())[4:10])
        job_results.append(table_i)
    # 获取运行中的job
    jobs = scheduler.get_jobs()
    run_jobs = []
    for i in jobs:
        cron_info_dict = dict()
        next_run_time = ""
        if hasattr(i, 'next_run_time'):
            next_run_time = str(i.next_run_time.strftime("%Y-%m-%d %H:%M:%S")) if i.next_run_time else ""
        if hasattr(i.trigger, 'fields'):
            for value in i.trigger.fields:
                cron_info_dict[str(value.name)] = str(value)
                # print(value.name,value)
        cron_info_val = list(cron_info_dict.values())
        cron_info_val.reverse()
        cron_info = " ".join(cron_info_val)
        run_jobs.append({
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
    return templates.TemplateResponse("index.html",
                                      {"request": request, 'run_jobs': run_jobs, 'job_results': job_results,
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
    query = sche.select().where(sche.c.id == job.id)
    result = await database.fetch_one(query)
    result_dict = dict(result)
    job_id = f'{job.id}_{int(time.time())}'
    try:
        scheduler.add_job(result_dict.get('script_name'),
                          trigger='cron',
                          id=job_id,
                          name=result_dict.get('schedule_name'),
                          misfire_grace_time=60 * 60,
                          coalesce=True,
                          max_instances=999,
                          second=result_dict.get("cron_second"),
                          minute=result_dict.get("cron_minutes"),
                          hour=result_dict.get("cron_hour"),
                          day=result_dict.get("cron_day_of_month"),
                          day_of_week=result_dict.get("cron_day_of_week"),
                          month=result_dict.get("cron_month"),
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
    query = sche.insert()
    values = dict(
        script_name=job.script_name,
        schedule_name=job.schedule_name,
        schedule_desc=job.schedule_desc,
        cron_second=job.cron_second,
        cron_minutes=job.cron_minutes,
        cron_hour=job.cron_hour,
        cron_day_of_month=job.cron_day_of_month,
        cron_day_of_week=job.cron_day_of_week,
        cron_month=job.cron_month,
        run_type=1,
        enabled=0,
        is_lock=1,
        priority=999,
        create_time=now,
    )
    await database.execute(query=query, values=values)

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
