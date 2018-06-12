FROM          python

COPY          . /app
WORKDIR       /app
RUN           python setup.py install
ENV           ASSET_DIR /asyncy

CMD           ["asyncy-server", "start"]
