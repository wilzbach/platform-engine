FROM          python

COPY          . /app
WORKDIR       /app
RUN           python setup.py install
ENV           ASSET_DIR /tmp
ENV           logger_level info

CMD           ["asyncy-server", "start"]
