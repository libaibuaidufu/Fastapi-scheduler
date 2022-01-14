FROM tiangolo/uvicorn-gunicorn-fastapi:python3.6
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY . /app
RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ -r /app/reqiurements.txt

