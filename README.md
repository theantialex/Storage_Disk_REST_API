# YandexDisk_REST_API

Backend for a file storage web service, similar to the [Yandex Disk](https://yandex.ru/disk) service, which allows users to upload and update information about files and folders. REST API service with a specification corresponding to the file <code>openapi.yaml</code>

The application and database are inside Docker containers.
There are two commands available inside the Docker container with the application:
 *   disk_app-db — utility for managing database state
 *   disk_app-api — utility for launching REST API service

Development
==========
Quick commands
---------------
* `make` Display a list of available commands
* `make devenv` Create and configure a virtual development environment
* `make postgres` Start Docker container with PostgreSQL
* `make clean` Delete files created by the module `distutils`_

Preparing the environment for development
---------------
```
    make devenv
    make postgres
    source env/bin/activate
    disk_app-db upgrade head
    disk_app-api
```
After running the commands, the application will start listening for requests on 0.0.0.0:8080.

Testing
---------------
Test coverage achieved 94%.

To run local testing, you must run the following commands:
```
    make devenv
    make postgres
    source env/bin/activate
    pytest
```
Server deployment
==========
```
  git clone https://github.com/theantialex/YandexDisk_REST_API.git
  cd YandexDisk_REST_API && docker-compose up -d
```
Once launched, the application will start listening for requests at 0.0.0.0:80.

## Setting up autorun on the server ##

After deployment on the server, you can configure the application to autostart when it is restarted. To do this, you need to place the docker-compose.service file in the /etc/systemd/system directory and
run the following commands:

```
  systemctl enable docker-compose
  systemctl start docker-compose
```
