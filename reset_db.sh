#!/bin/bash

rm -r ./migrations
rm ./app.db
flask db init
flask db migrate
flask db upgrade
python db_setup.py
echo "DB setup complete"