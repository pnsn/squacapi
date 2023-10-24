<img alt="Squacapi" class="right" src="./blue_squacLogo_rgb_med.png" />

# SQUACapi - Seismic Quality Assesment Console API 

[![Build Status](https://travis-ci.com/travis-ci/travis-web.svg?branch=master)](https://travis-ci.com/travis-ci/travis-web)

Squacapi is an open source application for reporting on seismic network performance. 

See [app_root]/swagger for full API documentation

Getting started:
populate .env
run docker-compose build
to get starter data:
docker-compose run --rm app sh -c "python manage.py bootstrap_db --days=7"