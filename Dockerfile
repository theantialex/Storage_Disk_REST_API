FROM snakepacker/python:all as builder

RUN python3.8 -m venv /usr/share/python3/app
RUN /usr/share/python3/app/bin/pip install -U pip

COPY requirements.txt /mnt/dist/
RUN /usr/share/python3/app/bin/pip install -Ur /mnt/dist/requirements.txt

COPY disk_app/ /mnt/dist/disk_app
COPY setup.py /mnt/dist/
COPY README.md /mnt/dist/

RUN /usr/share/python3/app/bin/pip install /mnt/dist/ \
    && /usr/share/python3/app/bin/pip check

RUN ln -snf /usr/share/python3/app/bin/disk_app-* /usr/local/bin/

ENV PYTHONPATH /mnt/dist/
