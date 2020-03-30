# Fastapi-scheduler

这是一个 fastapi 结合 apscheduler 做的一个动态添加定时任务的web

## 快速使用：

1. 导入 scheduler.sql 到 mysql

2. 启动 aps-server.py

   ```
   python aps-server.py
   ```

3. 启动 main.py

   ```
   python main.py
   ```

4. 打开 http://localhost:8081

## 已实现功能：

- 存储配置到 mysql，并实现增删该查
- 实时修改运行中的任务
- 上传脚本 及查看脚本列表

## 后期加入功能：

- 分页
- 脚本下载，上传文件夹
- 加入 jobstore (原因 本来已经加入了 ，结果在执行我自己的一个脚本时，出现pickle 错误就战时没有加入,可以自己在 aps_server.py 中配置)
- 配置脚本初始化参数 args,kwargs



## 已知问题：

- 脚本执行后，对脚本修改，再次执行可能无效。（原因可能是 第一次已经对脚本进行加载无法再次更新）
- 执行 class 类时，用函数在外面运行最好 ，类似 example_class.py



## 预览

 ![image](https://github.com/libaibuaidufu/Fastapi-scheduler/blob/master/doc_img.png) 

