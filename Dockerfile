FROM          python

COPY          . /app
WORKDIR       /app
RUN           python setup.py install

CMD           ["celery", "worker", "-A", "asyncy.CeleryTasks"]
