#!/bin/bash

sudo service mysql start
sudo service redis-server start

act() {
    source venv/bin/activate
}

m() {
    python manage.py migrate
}

mm() {
    python manage.py makemigrations
}

run() {
    python manage.py runserver
}

shell() {
    python manage.py shell
}

gp() {
    git push && git checkout dev && git merge test && git push && git checkout test
}