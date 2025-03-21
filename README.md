vCenter Lookup Bridge API
==================

The vCenter Lookup Bridge API connects to vCenter and provides the following resource information via the REST API.

* Virtual machines
* Datastores
* Portgroups

## Requirement
* Python 3.12 or later
* fastapi 0.115 or later
* pyvmomi 8.0.3 or later
* vsphere automation sdk for python 8.0.3 or later

## Contents

``` contents
vcenter-lookup-bridge
├── LICENSE
├── Dockerfile
├── README.md: this document
├── app
│    └── src
│         ├── config
│         │    ├── uvicorn_log_config.yml: config file for uvicorn
│         │    ├── vcenter_lookup_bridge.yml: config file
│         │    └── vcenters
│         │         └── vcenter.example.com.yml.sample: sample config forvCenter settings
│         ├── log
│         │    ├── access.log: HTTP access log
│         │    ├── error.log: error log
│         │    └── vcenter_lookup_bridge.log: general information log
│         ├── main.py: main script
│         ├── requirements.txt: dependent modules
│         └── vcenter_lookup_bridge
│              ├── api
│              │    └── routes
│              ├── schemas
│              ├── utils
│              └── vmware
├── docker-compose.override.yml.sample
├── docker-compose.yml
├── docs: other documents
└── pip.conf
```

## How to setup / docker compose
1. copy docker-compose.override.yml
```bash
$ cp docker-compose.override.yml.sample docker-compose.override.yml
```

2. edit docker-compose.override.yml
```bash
$ vi docker-compose.override.yml
services:
  api:
    environment:
      # Redis server hostname (Change this only if you are using an external Redis server)
      #- VLB_CACHE_HOSTNAME=cache

      # Redis server port number (Change this only if you are using an external Redis server)
      #- VLB_CACHE_PORT=6379

      # The time (in seconds) to cache the results of a request.
      - VLB_CACHE_EXPIRE_SECS=60

      # Function logger Enable／Dsiable
      - VLB_FUNC_LOGGER_ENABLED=True

      # Function logger Include arguments in the output
      - VLB_FUNC_LOGGER_ARGS_OUTPUT=False

      # Function logger When including arguments in the output,
      # limit the maximum length of each argument
      - VLB_FUNC_LOGGER_ARGS_LENGTH_MAX=20

      # Log Directory
      - VLB_LOG_DIR=/app/log

      # Log File name
      - VLB_LOG_FILE=vcenter_lookup_bridge.log

      # Log level
      - VLB_LOG_LEVEL=INFO

    #labels:
      # BASIC authentication is enabled using the traefik (reverse proxy) function.
      # By default, the following user name and password are set.
      #   Username: apiuser, Password: P@ssw0rd
      # The value of traefik.http.middlewares.vcenter_lookup_bridge_auth.basicauth.users is a string in htpassword format.
      # Please change it as necessary.
      # ex. $ htpasswd new_user new_password
      #- "traefik.http.middlewares.vcenter_lookup_bridge_auth.basicauth.users=apiuser:$$apr1$$zFHk.cXh$$01OU2XMdDq/OjlunHPCCn/"
      #- "traefik.http.routers.vcenter_lookup_bridge.middlewares=vcenter_lookup_bridge_auth"
```

3. copy vcenter configuration
```bash
$ cp app/config/vcenter.example.com.yml.sample app/config/your-vcenter.yml
```

4. edit vcenter configuration
```bash
$ vi app/config/your-vcenter.yml
# Identifier
name: "your-vcenter"

# vCenter Hostname/IP
hostname: "vcenter.example.com"
# vCenter port
port: 443

# vCenter user
username: "ansible@vsphere.local"
# vCenter password
password: "P@ssw0rd"

# Specify whether to validate certificates when making TLS connections to vCenter
# Specify False if you do not use certificates from the public authentication period
#   True: verify, False: do not verify
ignore_ssl_cert_verify: True

# Parent folder when searching virtual machine folders
# Only virtual machine folders under this folder are searched.
base_vm_folder: "D-V"

```

5. build docker image
```bash
$ docker compose build
```

6. run containers
```bash
$ docker compose up -d
```

## How to use

You can use the API by accessing the following URL.
  http://your-server/api/v1/

You can also view the API documentation by accessing the following URL in your browser.
  http://your-server/api/v1/docs
