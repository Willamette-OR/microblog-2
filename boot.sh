#!/bin/sh
source activate ./venv
flask db upgrade
flask translate compile
exec gunicorn -b :5000  --access-logfile - --error-logfile - microblog:app