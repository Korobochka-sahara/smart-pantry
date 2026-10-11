Smart Pantry — текущее состояние проекта
1. Цель проекта
Smart Pantry — backend для приложения учёта продуктов в домашнем хозяйстве.
Основная идея:
- пользователь регистрируется и авторизуется;
- создаёт household;
- добавляет участников;
- household имеет общий запас продуктов;
- продукты представлены глобальными Product;
- конкретные запасы household представлены InventoryItem;
- пользователь может отмечать продукты как отслеживаемые через TrackedProduct;
- отслеживание позволяет определять низкий запас;
- в дальнейшем пользователь фотографирует чек;
- система распознаёт чек через OCR;
- распознанные товары сопоставляются с существующими Product;
- после подтверждения данные из чека добавляются в inventory.
Главная архитектурная идея:
Android Client
      ↓
   REST API
      ↓
   FastAPI
      ↓
   Services
      ↓
 SQLAlchemy ORM
      ↓
 PostgreSQL
API должен оставаться тонким: HTTP-обработка находится в api, бизнес-правила — в services.
2. Технологический стек
Backend:
- Python 3.11
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL 16
- psycopg
- JWT
- Argon2 через pwdlib
- python-dotenv
- REST API
- JSON
Планируемые компоненты:
- OCR
- алгоритмы нормализации текста
- fuzzy matching / similarity
- возможно embeddings / ML на последующих этапах
- Android client на Kotlin + Jetpack Compose
- в дальнейшем возможно Redis/Celery для фоновых задач.
3. Структура backend
Текущая архитектура:
backend/
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── household.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   └── tracked_product.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── ...
│   │
│   ├── enums/
│   │   ├── household.py
│   │   └── ...
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── household.py
│   │   ├── household_member.py
│   │   ├── product.py
│   │   ├── inventory_item.py
│   │   └── tracked_product.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── household.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   └── tracked_product.py
│   │
│   ├── services/
│   │   ├── auth.py
│   │   ├── household.py
│   │   ├── product.py
│   │   ├── inventory.py
│   │   ├── tracked_product.py
│   │   └── auxiliary_functions.py
│   │
│   ├── security.py
│   └── main.py
│
├── alembic/
├── tests/
├── .env
├── .env.example
└── ...
Принцип:
api
 ↓
services
 ↓
models / database
api отвечает за HTTP:
- path/query/body;
- authentication dependency;
- HTTP status codes;
- преобразование domain errors → HTTP errors.
services отвечает за бизнес-логику.
4. Database
Основные таблицы:
user
household
household_member
product
inventory_item
tracked_product
refresh_token
inventory_event был удалён из проекта и больше не существует.
Это важно: текущая архитектура не должна предполагать наличие InventoryEvent.
5. Authentication
Реализованы:
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
Используется:
- password hashing через Argon2;
- JWT access token;
- JWT refresh token;
- сохранение refresh token в БД в виде hash;
- rotation;
- revocation;
- logout.
Refresh token имеет:
id
user_id
token_hash
expires_at
created_at
revoked_at
Тесты authentication полностью проходят.
6. Household
Household принадлежит пользователям через:
household_member
а не через household.owner_id.
Роли:
OWNER
ADMIN
MEMBER
Создатель household автоматически становится OWNER.
Правила:
OWNER
Может:
- добавлять пользователей;
- менять роли;
- удалять участников;
- покидать household;
- передавать ownership через механизм выхода.
ADMIN
Может:
- добавлять пользователей;
- изменять/удалять MEMBER.
Не может:
- менять OWNER;
- менять другого ADMIN;
- назначать OWNER.
MEMBER
Не может управлять участниками.
При выходе OWNER:
1. если есть ADMIN → OWNER становится подходящий ADMIN;
2. если ADMIN нет → выбирается MEMBER;
3. выбор выполняется по username;
4. если OWNER был один → household удаляется.
Ограничения:
- пользователь может создать максимум 5 household;
- в household ограничено количество участников согласно текущей реализации.
7. Product
Product — глобальное описание продукта, а не запас конкретного household.
Например:
Product:
Milk 3.2%
barcode = ...
brand = ...
unit = L
Один Product может использоваться в разных household.
Основные поля:
id
barcode
name
brand
category
unit
package_quantity
package_unit
created_at
updated_at
barcode nullable, но если указан — уникален.
Реализованы:
POST /products
GET  /products/{id}
GET  /products/search
Поиск поддерживает:
- name;
- brand;
- barcode;
- регистронезависимый поиск;
- несколько результатов.
8. Inventory
InventoryItem — конкретный запас продукта в конкретном household.
Концептуально:
Product
   ↓
InventoryItem
   ↓
Household
Например:
Product:
Milk 3.2%

Household A:
InventoryItem
quantity = 2

Household B:
InventoryItem
quantity = 7
То есть количество принадлежит именно household, а не Product.
quantity хранится как Numeric, поскольку должны поддерживаться как целые количества:
3 упаковки
5 штук
так и дробные:
0.5 kg
1.25 L
Текущий backend поддерживает:
- создание;
- получение;
- получение списка;
- изменение;
- удаление;
- дробные значения;
- 0;
- валидацию отрицательных значений;
- ограничения точности/scale;
- проверку существования Product.
Очень важная архитектурная гарантия:
Пользователь должен иметь membership в household, чтобы работать с его inventory.

Нельзя просто принять household_id из URL и довериться ему.
9. TrackedProduct
TrackedProduct связывает Product с household для отслеживания запасов.
Например:
Household A
    ↓
TrackedProduct
    ↓
Milk
minimum_quantity = 2
Low-stock определяется через Invent