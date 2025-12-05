# Установка Redis для Windows

## Вариант 1: WSL (рекомендуется)

Если у вас установлен WSL (Windows Subsystem for Linux):

```bash
wsl
sudo apt update
sudo apt install redis-server
redis-server
```

## Вариант 2: Docker

Если у вас установлен Docker:

```bash
docker run -d -p 6379:6379 redis:latest
```

## Вариант 3: Memurai (Redis для Windows)

1. Скачайте Memurai с https://www.memurai.com/
2. Установите и запустите
3. По умолчанию работает на localhost:6379

## Вариант 4: Временно отключить Celery

Если Redis не нужен для разработки, можно временно отключить Celery (см. ниже)

