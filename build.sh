#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python bankapp/manage.py migrate
python bankapp/manage.py collectstatic --noinput
