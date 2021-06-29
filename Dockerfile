FROM continuumio/miniconda3:4.9.2-alpine

RUN adduser -D microblog

WORKDIR /home/microblog

COPY requirements.txt requirements.txt
RUN conda create --prefix ./venv
RUN conda install --prefix ./venv -c conda-forge --file requirements.txt 
RUN venv/bin/pip install guess-language-spirit==0.5.3
RUN conda install --prefix ./venv/ gunicorn

COPY app app
COPY migrations migrations
COPY microblog.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP microblog.py

RUN chown -R microblog:microblog ./
USER microblog

EXPOSE 5000
ENTRYPOINT [ "./boot.sh" ]