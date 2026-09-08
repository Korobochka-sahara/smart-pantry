# Smart Pantry — полное описание проекта

## 1. Назначение проекта

Smart Pantry — pet project для управления домашними запасами продуктов.

Основная идея приложения:

пользователь создаёт одно или несколько домохозяйств (households), добавляет туда участников и совместно с ними ведёт учёт продуктов.

Приложение должно позволять:

* создавать household;
* приглашать/добавлять пользователей;
* назначать роли;
* хранить продукты;
* учитывать количество продуктов;
* отслеживать сроки годности;
* отслеживать открытые продукты;
* вести историю изменений количества;
* отслеживать продукты, которые заканчиваются;
* сканировать чеки;
* распознавать товары с помощью OCR;
* сопоставлять распознанные товары с существующими продуктами;
* отправлять уведомления;
* в будущем поддерживать Android-приложение как основной клиент.

Проект одновременно является практическим pet project и способом продемонстрировать навыки backend-разработки, работы с БД, API, authentication, ORM, миграциями, ML/OCR и Android.

---

# 2. Технологический стек

## Backend

Язык:

Python

Framework:

FastAPI

ORM:

SQLAlchemy 2.x

Миграции:

Alembic

База данных:

PostgreSQL 16

Authentication:

JWT

Пароли:

Argon2 через pwdlib

Переменные окружения:

python-dotenv

HTTP API:

REST

---

# 3. Frontend

Планируется Android-приложение.

Основной стек:

* Kotlin
* Jetpack Compose

Android-приложение будет обращаться к FastAPI backend через HTTP API.

Frontend не должен содержать бизнес-логику, которая должна выполняться на сервере.

Например, правила:

* максимум 5 созданных households;
* максимум 20 участников;
* кто может менять роли;
* кто становится новым OWNER;

должны проверяться backend.

Android-клиент должен только отображать результат API и отправлять запросы.

---

# 4. Инфраструктура разработки

PostgreSQL запускается в Docker.

Контейнер базы данных:

smart-pantry-postgres

PostgreSQL внутри контейнера использует стандартный порт 5432.

На Windows локальный PostgreSQL уже занимает 5432, поэтому Docker PostgreSQL опубликован на:

5433

Таким образом:

Windows host
↓
localhost:5433
↓
Docker
↓
PostgreSQL:5432

---

# 5. Переменные окружения

Backend использует `.env`.

Пример:

DATABASE_URL=postgresql://smart_pantry:smart_pantry_password@localhost:5433/smart_pantry
SECRET_KEY=<secret>

`.env` нельзя коммитить в Git.

В репозитории есть `.env.example` с шаблоном переменных без настоящих секретов.

SECRET_KEY в будущем необходимо заменить на новый, если старый секрет когда-либо публиковался в истории проекта или сообщениях.

---

# 6. Структура backend

Текущая структура:

backend/
├── app/
│   ├── api/
│   │   ├── **init**.py
│   │   ├── auth.py
│   │   └── household.py
│   │
│   ├── db/
│   │   └── database.py
│   │
│   ├── enums/
│   │   ├── **init**.py
│   │   └── household.py
│   │
│   ├── models/
│   │   ├── category.py, household_member.py, household.py, inventory_event.py, inventory_item.py, product.py,              |   |         receipt_item.py, receipt.py, refresh_token.py, tracked_product.py, user.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   └── household.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   └── household_service.py
│   │
│   ├── security.py
│   └── main.py
│
├── alembic/
│   ├── env.py
│   └── versions/
│
└── .env

Архитектурная идея:

api
↓
services
↓
models / database

API отвечает за HTTP.

Services отвечают за бизнес-логику.

Models описывают структуру БД.

Schemas описывают входные и выходные данные API.

---

# 7. Database layer

`app/db/database.py` отвечает за:

* загрузку DATABASE_URL;
* создание SQLAlchemy engine;
* создание SessionLocal;
* определение Base;
* dependency `get_db`.

DATABASE_URL преобразуется из:

postgresql://

в:

postgresql+psycopg://

чтобы SQLAlchemy использовал psycopg.

Основной паттерн:

def get_db():
db = SessionLocal()
try:
yield db
finally:
db.close()

FastAPI endpoint получает Session через:

db: Session = Depends(get_db)

---

# 8. Database schema

Основные таблицы:

* user
* household
* household_member
* category
* product
* inventory_item
* receipt
* receipt_item
* tracked_product
* inventory_event
* refresh_token

---

# 9. User

Таблица `user` хранит пользователей.

Основные поля:

* id
* email
* username
* password_hash
* created_at

Email уникальный.

Username уникальный.

Пароль никогда не хранится в открытом виде.

Хранится Argon2 hash.

---

# 10. Household

Household — отдельное домохозяйство/пространство для совместного учёта продуктов.

Поля:

* id
* name
* created_at
* updated_at

У Household намеренно нет `owner_id`.

Владелец определяется через таблицу:

household_member

и роль:

OWNER

Это позволяет хранить ownership как часть membership-модели.

---

# 11. HouseholdMember

Таблица связывает пользователей и households.

Поля:

* id
* household_id
* user_id
* role
* joined_at

Есть unique constraint:

(household_id, user_id)

Один пользователь не может дважды состоять в одном household.

Также используется PostgreSQL ENUM:

household_role

со значениями:

OWNER
ADMIN
MEMBER

---

# 12. Правила Household

Один пользователь может создать максимум:

5 households.

При этом пользователь может состоять максимум в:

100 households.

Эти ограничения являются бизнес-правилами backend.

Количество созданных households определяется по membership с ролью OWNER.

Отдельный счётчик не хранится.

---

# 13. Роли

## OWNER

Полный контроль над household.

OWNER может:

* добавлять пользователей;
* менять роли;
* удалять пользователей;
* передавать ownership через предусмотренную логику;
* покидать household.

Если OWNER покидает household:

1. выбирается ADMIN с минимальным username в алфавитном порядке;
2. если ADMIN нет — выбирается MEMBER с минимальным username;
3. выбранный пользователь становится OWNER;
4. старый OWNER покидает household.

Если других участников нет:

* удаляется membership;
* удаляется household.

---

## ADMIN

ADMIN может:

* добавлять пользователей;
* менять роли MEMBER;
* удалять MEMBER.

ADMIN не может:

* изменить OWNER;
* удалить OWNER;
* изменить другого ADMIN;
* удалить другого ADMIN;
* назначить OWNER.

---

## MEMBER

MEMBER может пользоваться household, но не может управлять участниками.

---

# 14. Household service

`household_service.py` содержит бизнес-логику household.

Используются доменные исключения:

HouseholdNotFoundError

HouseholdPermissionError

HouseholdConflictError

Они преобразуются API-слоем в:

404
403
409

соответственно.

---

# 15. Household service helpers

Для уменьшения дублирования используются helpers.

`get_household_member(...)`

Находит membership текущего пользователя.

Если пользователь не является участником:

HouseholdNotFoundError.

`get_target_member(...)`

Находит membership целевого пользователя.

Если пользователь не является участником:

HouseholdNotFoundError.

`require_household_role(...)`

Проверяет, что роль пользователя входит в список разрешённых ролей.

Например:

require_household_role(
member,
HouseholdRole.OWNER,
HouseholdRole.ADMIN,
)

означает:

действие доступно OWNER и ADMIN.

---

# 16. Household API

Prefix:

/households

Основные endpoint:

POST /households

Создание household.

GET /households

Получение households текущего пользователя.

GET /households/{household_id}

Получение household, если текущий пользователь является его участником.

GET /households/{household_id}/members

Получение списка участников.

POST /households/{household_id}/members

Добавление пользователя.

PATCH /households/{household_id}/members/{target_user_id}/role

Изменение роли.

DELETE /households/{household_id}/members/{target_user_id}

Удаление пользователя.

POST /households/{household_id}/leave

Выход текущего пользователя.

---

# 17. Authentication

Authentication реализован через JWT.

Используются два типа токенов:

access token

refresh token

---

# 18. Access token

Access token используется для доступа к защищённым API.

Содержит:

sub = user id

exp = expiration

Алгоритм:

HS256

Текущий срок жизни:

60 минут.

Клиент отправляет:

Authorization: Bearer <access_token>

FastAPI dependency:

get_current_user

извлекает токен, декодирует JWT и получает пользователя из БД.

---

# 19. Refresh token

Refresh token нужен, чтобы пользователь не логинился заново после истечения access token.

Срок жизни:

30 дней.

Refresh token также хранится в БД, но не в открытом виде.

В БД хранится SHA-256 hash токена.

Таблица:

refresh_token

Поля:

* id
* user_id
* token_hash
* expires_at
* created_at
* revoked_at

---

# 20. Refresh token rotation

При `/auth/refresh`:

1. проверяется JWT;
2. проверяется type = refresh;
3. извлекается user_id;
4. вычисляется hash токена;
5. ищется соответствующая запись в БД;
6. проверяется expiration;
7. проверяется revoked_at;
8. старый refresh token revoke;
9. создаётся новый access token;
10. создаётся новый refresh token;
11. новый refresh token сохраняется в БД.

Таким образом используется rotation.

---

# 21. Logout

POST:

/auth/logout

Logout revoke-ит refresh token.

Access token не удаляется сервером.

Он продолжает работать до expiration.

Это нормальная модель для текущей реализации.

Android-клиент после logout должен удалить локально сохранённые токены.

---

# 22. Authentication endpoints

POST /auth/register

Регистрация.

POST /auth/login

Login.

POST /auth/refresh

Обновление токенов.

POST /auth/logout

Logout.

GET /auth/me

Получение текущего пользователя.

---

# 23. Password validation

Пароль должен:

* содержать минимум 8 символов;
* содержать uppercase;
* содержать lowercase;
* содержать digit.

Пароль хэшируется через Argon2.

---

# 24. Product

`product` представляет сам продукт как сущность.

Это не конкретная пачка продукта в доме.

Например:

Product:

"Milk 3.2%"

может существовать один раз.

А конкретные запасы молока пользователя будут представлены через:

InventoryItem.

Поля Product:

* id
* barcode
* name
* brand
* category_id
* unit
* package_quantity
* package_unit
* created_at
* updated_at

Barcode индексируется и может быть NULL.

---

# 25. Category

Category предназначена для классификации продуктов.

Например:

* Dairy
* Meat
* Vegetables
* Fruits
* Drinks
* Snacks
* Frozen
* Canned
* Other

Точная система категорий ещё может быть доработана.

---

# 26. InventoryItem

InventoryItem — конкретный запас продукта в household.

Например:

Product:
Milk

InventoryItem:

household = Maria's household
quantity = 2
unit = package
expiry_date = ...

Таким образом:

Product отвечает на вопрос:

"Что это за продукт?"

InventoryItem:

"Сколько этого продукта сейчас есть в конкретном household?"

---

# 27. InventoryItem fields

Основные поля:

* id
* household_id
* product_id
* quantity
* unit
* purchase_date
* expiry_date
* opened_at
* status
* created_at
* updated_at

Количество использует Numeric.

Это важно, потому что продукты могут измеряться не только целыми штуками.

Например:

0.5 kg

1.25 L

2 units

---

# 28. Inventory status

InventoryItem должен поддерживать состояния продукта.

Например:

ACTIVE
OPENED
EXPIRED
DEPLETED

Точная enum-модель может быть уточнена при реализации inventory.

Важно отделять:

'количество' от 'статуса'.

Например продукт может иметь quantity = 1, но быть OPENED.

---

# 29. Inventory events

Таблица:

inventory_event

предназначена для истории изменения запасов.

Поля:

* inventory_item_id
* user_id
* event_type
* quantity_change
* created_at

Примеры событий:

ADD

REMOVE

USE

ADJUST

OPEN

EXPIRE

Конкретный набор event types можно окончательно определить при реализации inventory.

Главная идея:

не просто хранить текущее quantity,

а иметь историю того, как оно изменялось.

Например:

10 → -1 → -2 → +5

История позволяет понимать:

кто изменил запас;

когда;

на сколько.

---

# 30. TrackedProduct

Таблица:

tracked_product

предназначена для продуктов, которые пользователь хочет отслеживать.

Поля:

* household_id
* product_id
* minimum_quantity
* created_at
* updated_at

Есть unique constraint:

(household_id, product_id)

Например:

Milk
minimum_quantity = 2

Когда количество становится <= 2, продукт считается нуждающимся в пополнении.

В будущем это может использоваться для:

* shopping list;
* уведомлений;
* автоматических рекомендаций.

---

# 31. Receipt

Receipt представляет чек покупки.

Поля:

* household_id
* user_id
* store_name
* purchase_date
* total_amount
* image_path
* created_at

Чек принадлежит household.

Пользователь может быть сохранён как тот, кто загрузил чек.

---

# 32. ReceiptItem

ReceiptItem — отдельная позиция из чека.

Поля:

* receipt_id
* product_id
* raw_name
* quantity
* unit_price
* total_price
* matching_confidence
* created_at

`raw_name` хранит исходное название, распознанное OCR.

`product_id` может быть NULL, если товар ещё не сопоставлен.

`matching_confidence` показывает уверенность алгоритма сопоставления.

---

# 33. OCR pipeline

Будущая архитектура обработки чека:

Фото чека
↓
OCR
↓
распознанный текст
↓
выделение товарных позиций
↓
нормализация названий
↓
matching с Product
↓
confidence score
↓
ReceiptItem
↓
подтверждение пользователем
↓
InventoryItem

Важно не считать OCR полностью достоверным.

OCR может:

* ошибиться в символе;
* неправильно разделить строки;
* спутать цену и количество;
* неправильно распознать название продукта.

Поэтому matching должен иметь confidence.

---

# 34. Product matching

Система должна сопоставлять OCR-название с существующими Product.

Например OCR:

"Молоко Простоквашино 3,2% 930мл"

может быть сопоставлено с:

Product:
"Молоко 3.2%"
Brand:
"Простоквашино"

Алгоритм matching в будущем может использовать:

* barcode;
* normalized name;
* brand;
* category;
* package size;
* fuzzy matching;
* embeddings/ML при необходимости.

Не следует сразу использовать сложную ML-модель.

Сначала лучше сделать deterministic/fuzzy baseline.

---

# 35. API architecture

Общая схема:

Android
↓
HTTP/JSON
↓
FastAPI
↓
API router
↓
Service
↓
SQLAlchemy
↓
PostgreSQL

API не должен напрямую содержать сложные SQL/business rules.

Например endpoint должен быть похож на:

current_user = Depends(get_current_user)

result = service_function(...)

return result

А сложные проверки должны находиться в service.

---

# 36. Pydantic schemas

Schemas используются для API contract.

Например HouseholdCreate:

name

HouseholdResponse:

id
name
created_at
updated_at

Nested member response:

user
role
joined_at

Для ORM objects используется:

ConfigDict(from_attributes=True)

---

# 37. Alembic

Alembic используется для изменения схемы БД.

Initial migration создала основные таблицы.

Последующие migrations:

* добавляли inventory event fields/index;
* добавляли refresh_token;
* добавляли PostgreSQL ENUM household_role;
* меняли household_member.role на этот ENUM.

При изменении моделей:

1. изменить SQLAlchemy model;
2. создать migration;
3. проверить migration;
4. применить upgrade;
5. проверить БД.

Нельзя просто изменять существующую БД вручную и считать это завершённым изменением.

---

# 38. PostgreSQL ENUM

HouseholdRole использует PostgreSQL enum:

household_role

Значения:

OWNER
ADMIN
MEMBER

SQLAlchemy:

Enum(
HouseholdRole,
name="household_role",
)

Важно, чтобы Alembic корректно создавал и изменял enum.

---

# 39. Current main.py

FastAPI application:

app = FastAPI(
title="Smart Pantry API",
version="0.1.0",
)

Подключены:

auth router
household router

Есть:

GET /

возвращающий:

{
"message": "Smart Pantry API",
"status": "OK"
}

---

# 40. Реализованное состояние проекта

На текущий момент уже работают:

* PostgreSQL;
* Docker database;
* SQLAlchemy;
* Alembic;
* User model;
* registration;
* login;
* password hashing;
* access JWT;
* refresh JWT;
* refresh token persistence;
* refresh rotation;
* logout/revocation;
* `/auth/me`;
* Household model;
* HouseholdMember;
* household roles;
* household creation;
* 5-household creation limit;
* 20-member limit;
* household listing;
* household access checking;
* member listing;
* adding members;
* role changes;
* member removal;
* leaving household;
* automatic ownership transfer;
* automatic household deletion when owner leaves alone.

Все эти функции уже тестировались через API и работают.

---

# 41. Следующий этап разработки

После household refactor логичный следующий большой блок:

PRODUCT + INVENTORY.

Рекомендуемый порядок:

1. Product model проверить/доделать.
2. Category.
3. Product schemas.
4. Product service.
5. Product API.
6. InventoryItem model.
7. Inventory schemas.
8. Inventory service.
9. Inventory CRUD.
10. Проверка household permissions для inventory.
11. Inventory events.
12. TrackedProduct.
13. Expiry logic.
14. Shopping/low-stock logic.
15. Receipt.
16. ReceiptItem.
17. OCR.
18. Product matching.
19. Notifications.
20. Redis/Celery.
21. Android client.
22. Tests.
23. Docker.
24. CI/CD.

---

# 42. Важный принцип разработки

Проект следует развивать постепенно.

Не нужно одновременно создавать:

OCR + Redis + Celery + FCM + Android + ML.

Сначала должна появиться стабильная backend domain model.

Рекомендуемый dependency order:

Authentication
↓
Households
↓
Products
↓
Inventory
↓
Inventory events
↓
Tracking
↓
Receipts
↓
OCR
↓
Notifications
↓
Async jobs
↓
Android

---

# 43. Что особенно важно при дальнейшем развитии

Каждый новый endpoint, работающий с household-owned данными, должен проверять membership.

Например:

GET /inventory

не должен просто делать:

select(InventoryItem)

Он должен ограничивать результаты household, к которым пользователь имеет доступ.

То же относится к:

* products, если они household-specific;
* inventory;
* tracked products;
* receipts;
* shopping lists.

Нельзя доверять `household_id`, переданному клиентом.

Backend всегда должен самостоятельно проверять:

current_user
+
household_id
↓
есть ли membership?

---

# 44. Security principles

Нельзя доверять Android-клиенту.

Все ограничения проверяются backend.

Нельзя доверять:

* user_id;
* role;
* household membership;
* quantity;
* ownership;
* permissions.

Например клиент не должен отправлять:

{
"user_id": 123,
"role": "OWNER"
}

и ожидать, что backend этому поверит.

Текущий пользователь определяется по JWT.

Роль определяется по БД.

---

# 45. Transaction principle

Изменение нескольких связанных объектов должно выполняться в одной транзакции.

Например создание household:

1. создать Household;
2. получить id через flush;
3. создать OWNER membership;
4. commit.

Ownership transfer:

1. выбрать нового owner;
2. изменить его role;
3. удалить старый membership;
4. commit.

Это должно происходить атомарно.

---

# 46. Возможные будущие улучшения

После базовой реализации можно улучшить:

* централизованные FastAPI exception handlers;
* dependency для получения HouseholdMember;
* transaction helpers;
* database locking для конкурентных ownership операций;
* repository layer, если services станут слишком большими;
* полноценные unit tests;
* integration tests;
* pagination;
* filtering;
* sorting;
* OpenAPI documentation;
* structured logging;
* Docker Compose;
* CI через GitHub Actions.

Не следует добавлять эти уровни заранее без необходимости.

---

# 47. Общий принцип архитектуры

Smart Pantry должен оставаться относительно простым CRUD/business application с отдельными ML-компонентами.

Основной backend:

Authentication

* authorization
* households
* products
* inventory
* receipts
* notifications

ML/OCR:

отдельный слой, который помогает распознавать и сопоставлять данные.

ML не должен управлять основной бизнес-логикой.

---

# 48. Как продолжать работу над проектом

При дальнейшем изменении проекта сначала нужно проверить:

1. какие модели уже существуют;
2. какие migrations уже применены;
3. какие endpoints уже работают;
4. какие business rules уже определены;
5. какие тесты уже существуют.

Нельзя переписывать существующую архитектуру без необходимости.

Если функция уже работает, изменение должно быть incremental.

При добавлении новой функции нужно определить:

* model;
* schema;
* service;
* API;
* migration;
* permissions;
* tests.

---

# 49. Текущее состояние

Household subsystem считается практически завершённой после текущего рефактора.

Следующий основной фокус:

PRODUCT + INVENTORY.

Первая задача следующего этапа:

проверить текущую модель Product и реализовать полноценный Product CRUD с учётом Category и barcode.

После этого перейти к InventoryItem и связать конкретные запасы с household и Product.

Главная цель ближайшего этапа:

получить рабочую цепочку:

User
↓
Household
↓
Product
↓
InventoryItem
↓
InventoryEvent

После появления этой цепочки приложение уже будет иметь основное ядро системы учёта продуктов.
