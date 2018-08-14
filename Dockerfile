FROM          python:3.6.6

RUN           apt-get update
RUN           apt-get install -y socat

COPY          . /app
WORKDIR       /app
RUN           chmod +x entrypoint.sh
RUN           python setup.py install
ENV           ASSET_DIR /asyncy
ENV           logger_level info

ENTRYPOINT    /app/entrypoint.sh