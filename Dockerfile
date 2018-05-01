FROM          python

COPY          . /app
WORKDIR       /app
RUN           python setup.py install

CMD           ["asyncy-server", "start"]
