# YandexDisk_REST_API

Бэкенд для веб-сервиса хранения файлов, аналогичный сервису [Яндекс Диск](https://yandex.ru/disk), который позволяет пользователям загружать и обновлять информацию о файлах и папках. Является REST API сервисом со спецификацией, соответсвующей файлу <code>openapi.yaml</code>

## Ссылка на сервис ##

Разработка
==========
Быстрые команды
---------------
* `make` Отобразить список доступных команд
* `make devenv` Создать и настроить виртуальное окружение для разработки
* `make postgres` Поднять Docker-контейнер с PostgreSQL
* `make clean` Удалить файлы, созданные модулем `distutils`_

Подготовка окружения для разработки
---------------
```
    make devenv
    make postgres
    source env/bin/activate
    disk_app-db upgrade head
    disk_app-api
```
После запуска команд приложение начнет слушать запросы на 0.0.0.0:8080.

Развертывание на сервере
==========
```
  git clone git@github.com:theantialex/YandexDisk_REST_API.git
  cd YandexDisk_REST_API && docker-compose up -d
```
После запуска приложение начнет слушать запросы на 0.0.0.0:80.

## Настройка автозапуска на сервере ##

После разрвертывания на сервере можно настроить автозапуск приложения при его рестарте. Для этого необходимо поместить файл docker-compose.service в директорию /etc/systemd/system и
выполнить следующие команды:

```
  systemctl enable docker-compose
  systemctl start docker-compose
```
