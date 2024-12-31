#!/bin/bash
rm -rf build service-api.zip etl.zip 
mkdir build
pip install -r app/requirements.txt -t build/ || exit 1
pip install --platform manylinux2014_x86_64 --target=build \
    --implementation cp --python-version 3.12 --only-binary=:all: --upgrade psycopg2-binary || exit 1
cp -R app/query app/lambda_function.py build/
cd build
zip -r ../service-api.zip .
cd ..

cp -R app/etl build/
cd build
zip -r ../etl.zip .
cd ..