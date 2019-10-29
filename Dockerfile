FROM          python:3.7.4

RUN           pip install pip-tools

# Install dependencies in separate layer for caching
WORKDIR       /app
COPY          ./requirements.txt /app
RUN           pip-sync

COPY          . /app/
RUN           python setup.py install

ENTRYPOINT    ["storyscript-server", "start"]
