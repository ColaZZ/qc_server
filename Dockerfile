FROM python:3.7.5
LABEL maintainer="YeMiao0715@163.com"
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt -i https://pypi.douban.com/simple
CMD python scripts/init_mysql.py && python run.py
EXPOSE 8080