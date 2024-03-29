# Fastapi-scheduler

这是一个 fastapi 结合 apscheduler 做的一个动态添加定时任务的web

## 快速使用：

**注意： 修改 main.py 或者 main_rpc_server.py 的 mysql连接**

**创建数据库**
修改```DATABASE_URL = f'mysql+pymysql://root:password@localhost:3306/dbname'```中的配置内容

**获取项目**

```bash
git clone  https://github.com/libaibuaidufu/Fastapi-scheduler.git
```

**1.本地启动：**

1. 启动 rpc-server.py

   ```bash
   cd rpc_server
   python rpc-server.py
   ```

2. 启动 main_rpc_server.py

   ```
   python main_rpc_server.py
   ```

3. 打开 http://localhost:8000

**2.docker部署：**

1. 使用 docker-compose

   ```
   docker-compose up -d
   ```

2. 打开：http://ip:8080

**3.删除项目：**

1. 删除 `docker-compose down`

**4.复制脚本、安装指定库及添加任务：**

1. 复制脚本到 rpc_server 容器里面

   ```bash
   docker cp xx.py rpc-server:/usr/src/app/scheduler_script/
   ```

2. 安装 脚本中使用到的 库

   ```bash
   docker exec -it rpc_server pip install xxx
   ```

3. 再到 web 中去添加任务 再启动任务后，查询有点慢。。。

## 已实现功能：

- 存储配置到 mysql，并实现增删该查
- 实时修改运行中的任务
- 上传脚本 及查看脚本列表

## 后期加入功能：

- 分页
- 脚本下载，上传文件夹
- 加入 jobstore (原因 本来已经加入了 ，结果在执行我自己的一个脚本时，出现pickle 错误就暂时没有加入,可以自己在 aps_server.py 中配置)
- 配置脚本初始化参数 args,kwargs

## 已知问题：

- 脚本执行后，对脚本修改，再次执行可能无效。（原因可能是 第一次已经对脚本进行加载无法再次更新）
- 执行 class 类时，用函数在外面运行最好 ，类似 example_class.py
- 拷贝 rpc_server 里面的脚本 ，如果执行报错后，就算修改后再次执行也会出错 ，所以只能修改文件名称 再次 拷贝使用。

## 预览

![image](https://github.com/libaibuaidufu/Fastapi-scheduler/blob/master/doc_img.png) 

