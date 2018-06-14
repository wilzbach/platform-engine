FROM          python

COPY          . /app
WORKDIR       /app
RUN           python setup.py install
ENV           ASSET_DIR /asyncy
ENV           logger_level info

CMD           ["asyncy-server", "start"]
