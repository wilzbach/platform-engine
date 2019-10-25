FROM          python:3.7.4

RUN           apt-get update && apt-get install -y socat
RUN           pip install pip-tools

# Optimization to not keep downloading dependencies on every build.
WORKDIR       /app
COPY          ./requirements.txt /app
RUN           pip-sync

COPY          . /app/
WORKDIR       /app
RUN           chmod +x entrypoint.sh
RUN           python setup.py install
ENV           ASSET_DIR /asyncy
ENV           logger_level info

ENTRYPOINT    ["/app/entrypoint.sh"]
