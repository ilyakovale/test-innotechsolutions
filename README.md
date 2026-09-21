# 3 КОНТЕЙНЕРА:
+ БД postgres на alpine
+ FASTAPI - свагер
+ keycloak - авторизация

## ЦЕЛЬ: ПОКАЗАТЬ РЕАЛИЗАЦИЮ АВТОРИЗАЦИИ С ПОДТВЕРЖДЕНИЕМ EMAIL

## Требования

- **Docker Desktop 4.39+** — нужен для команды `pre_start` в compose-файле.
  На более старых версиях проект не соберётся.

## Запуск

```bash
docker compose up
```
Никаких ручных шагов — базы, Realm, SMTP и клиент настраиваются
автоматически при первом старте.


## Доступ
+ Swagger UI	http://localhost:8000/docs
+ Keycloak Admin	http://localhost:8080/

## Что сделано:

### Keycloak:
+ Realm test импортируется из JSON при старте
+ Открыта регистрация, вход по email
+ Включено подтверждение email — письмо приходит на почту
+ SMTP настроен через setup_keycloak.py (данные из .env)
+ Клиент fastapi — публичный, PKCE S256

### FastAPI:
+ Авторизация через fastapi-keycloak-middleware
+ Swagger UI с кнопкой Authorize (Authorization Code + PKCE)
+ Разграничение ролей — админская ручка проверяет роль admin из токена
+ CRUD вынесен в отдельные модули: crud.py, models.py, schemas.py, database.py

### PostgreSQL:
+ Две изолированные базы на одном сервере: keycloak_db и fastapi_db
+ Базы и пользователи создаются автоматически через init-db.sh

## Ручки
+ GET	/	все	Healthcheck
+ POST	/public	все	Пишет сообщение в БД без пользователя
+ POST	/authorize	JWT	Пишет сообщение с именем пользователя
+ GET	/admin	JWT + роль admin	Возвращает все сообщения с пометкой авторизации

## Как выдать роль admin
Users → выбрать пользователя → Role mapping → Assign role → admin


## Сценарий проверки:
1. Открыть http://localhost:8000/docs
2. Нажать Authorize → Authorize в диалоге → редирект на Keycloak
3. На странице входа нажать Register → зарегистрироваться
4. Перейти по ссылке из письма → вернуться в Swagger авторизованным
5. POST /authorize — сообщение запишется с именем
6. GET /admin — вернёт 403, пока нет роли admin
7. Выдать роль, перелогиниться → GET /admin покажет все сообщения