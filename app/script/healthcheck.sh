#/bin/bash

/usr/bin/curl -s "http://127.0.0.1:8000/api/v1/healthcheck/" -o /dev/null -w '%{http_code}\n' | grep '^200$'

