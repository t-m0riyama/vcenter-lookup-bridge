FROM python:3.12

RUN DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y tzdata \
    && apt-get clean

RUN mkdir /root/.pip
COPY ./app /app
COPY ./pip.conf /root/.pip/pip.conf
RUN pip install -U pip \
    && pip install -r /app/requirements.txt

WORKDIR /app

CMD gunicorn main:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile ./log/access.log \
    --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(b)s %(D)s' \
    --error-logfile ./log/error.log \
    --log-level info \
    --timeout 120
