FROM          python

COPY          . /app
WORKDIR       /app
RUN           python setup.py install
ENV           ASSET_DIR /tmp

CMD           ["asyncy-server", "start"]
