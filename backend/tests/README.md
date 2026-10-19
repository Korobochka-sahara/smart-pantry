# Backend tests

Тесты используют `pytest`, `FastAPI TestClient` и отдельную PostgreSQL-базу, URL которой задаётся в `backend/.env.test`. В `conftest.py` создаются таблицы на время сессии, очищаются перед каждым тестом и подменяется dependency `get_db`.

## Подготовка

Установи зависимости из `backend/requirements.txt`, запусти PostgreSQL и один раз создай тестовую БД, если её ещё нет:

```powershell
docker exec -it smart-pantry-postgres psql -U smart_pantry -d smart_pantry -c "CREATE DATABASE smart_pantry_test;"
```

Проверь, что `DATABASE_URL` в `.env.test` указывает именно на `smart_pantry_test`. Никогда не запускай тесты против рабочей базы: фикстура очищает таблицы.

## Запуск

Из каталога `backend/` с активным `.venv`:

```powershell
python -m pytest tests -v
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_inventory.py -v
python -m pytest tests/test_ocr.py -v
```

## Состав

- `test_auth.py` — регистрация, вход, JWT, refresh и logout.
- `test_household.py` — домохозяйства, роли и ограничения доступа.
- `test_product.py` — каталог и поиск товаров.
- `test_inventory.py` — создание, обновление, удаление запасов и изоляция домохозяйств.
- `test_tracked_product.py` — минимальные остатки и low-stock.
- `test_product_matching.py` — сопоставление позиций чека с каталогом.
- `test_ocr.py` — контракт OCR endpoint и ошибки загрузки.
- `conftest.py` — тестовая БД, TestClient и повторно используемые фикстуры.

Если тестовый файл отсутствует в текущей ветке, пропусти команду для него.

# 1. Auth — 9 тестов
1. test_register_user — успешная регистрация пользователя.
2. test_register_duplicate_email — нельзя зарегистрировать второго пользователя с тем же email.
3. test_register_duplicate_username — нельзя зарегистрировать второго пользователя с тем же username.
4. test_login_wrong_password — неправильный пароль не позволяет войти.
5. test_login_success — успешный логин возвращает токены.
6. test_get_current_user — авторизованный пользователь может получить свои данные через /auth/me.
7. test_get_current_user_without_token — /auth/me без токена возвращает отказ.
8. test_refresh_token — refresh token позволяет получить новый access token.
9. test_logout — после logout refresh token больше нельзя использовать.

# 2. Household — 22 теста
1. test_create_household — пользователь может создать household.
2. test_create_household_without_token — создать household без авторизации нельзя.
3. test_get_my_households — пользователь получает список своих household.
4. test_get_household — пользователь может получить свой household.
5. test_get_nonexistent_household — запрос несуществующего household возвращает 404.
6. test_user_cannot_access_foreign_household — пользователь не может получить чужой household.
7. test_creator_is_owner — создатель household получает роль OWNER.
8. test_get_household_members — участник может получить список участников household.
9. test_owner_can_add_member — OWNER может добавить участника.
10. test_member_cannot_add_member — MEMBER не может добавлять участников.
11. test_outsider_cannot_get_members — посторонний пользователь не может получить список участников.
12. test_owner_can_change_member_role — OWNER может изменить роль участника.
13. test_member_cannot_change_roles — MEMBER не может менять роли.
14. test_admin_cannot_change_owner_role — ADMIN не может менять роль OWNER.
15. test_owner_can_remove_member — OWNER может удалить участника.
16. test_member_cannot_remove_member — MEMBER не может удалять участников.
17. test_member_can_leave_household — обычный участник может самостоятельно выйти.
18. test_owner_leaves_and_admin_becomes_owner — при выходе OWNER ownership переходит подходящему ADMIN.
19. test_owner_alone_leaves_household — если OWNER единственный участник, household удаляется.
20. test_user_can_create_max_five_households — проверяется ограничение в 5 созданных household.
21. test_add_nonexistent_user — нельзя добавить несуществующего пользователя.
22. test_add_member_to_nonexistent_household — нельзя добавить участника в несуществующий household.

# 3. Product — 10 тестов
1. test_create_product — успешное создание Product.
2. test_create_product_without_barcode — Product может существовать без barcode.
3. test_create_product_duplicate_barcode — barcode должен быть уникальным.
4. test_get_product — получение существующего Product.
5. test_get_nonexistent_product — получение несуществующего Product возвращает 404.
6. test_search_product_by_name — поиск по названию.
7. test_search_product_by_brand — поиск по бренду.
8. test_search_product_by_barcode — поиск по barcode.
9. test_search_product_case_insensitive — поиск не зависит от регистра.
10. test_search_products_returns_multiple_results — поиск может вернуть несколько продуктов.

# 4. Inventory — 28 тестов
1. test_create_inventory_item — создание InventoryItem.
2. test_get_inventory_item — получение конкретного InventoryItem.
3. test_get_nonexistent_inventory_item — обработка несуществующего InventoryItem.
4. test_create_inventory_item_increases_existing_quantity — повторное добавление продукта увеличивает количество.
5. test_update_inventory_item_replaces_quantity — PATCH заменяет количество.
6. test_update_inventory_item_without_quantity_does_not_change_quantity — PATCH без quantity сохраняет старое количество.
7. test_create_inventory_item_with_nonexistent_product — нельзя создать inventory для несуществующего Product.
8. test_create_inventory_item_with_zero_quantity — разрешено количество 0.
9. test_create_inventory_item_with_negative_quantity — отрицательное количество запрещено.
10. test_update_inventory_item_with_negative_quantity — нельзя изменить количество на отрицательное.
11. test_update_inventory_item_to_zero — количество можно изменить на 0.
12. test_delete_inventory_item — удаление InventoryItem.
13. test_delete_nonexistent_inventory_item — обработка удаления несуществующего item.
14. test_get_household_inventory — получение всего inventory household.
15. test_get_empty_household_inventory — пустой household возвращает пустой список.
16. test_user_cannot_access_another_household_inventory — нельзя получить inventory чужого household.
17. test_user_cannot_get_inventory_item_from_another_household — нельзя получить конкретный чужой item.
18. test_user_cannot_update_another_household_inventory — нельзя изменить чужой item.
19. test_user_cannot_delete_another_household_inventory — нельзя удалить чужой item.
20. test_household_inventory_is_isolated — inventory разных household не смешивается.
21. test_get_inventory_from_nonexistent_household — получение inventory несуществующего household обрабатывается корректно.
22. test_create_inventory_in_nonexistent_household — нельзя создать inventory в несуществующем household.
23. test_create_inventory_with_zero_product_id — product_id = 0 отклоняется.
24. test_create_inventory_with_negative_product_id — отрицательный product_id отклоняется.
25. test_create_inventory_with_too_many_decimal_places — проверяется допустимое количество знаков после запятой.
26. test_update_inventory_with_too_many_decimal_places — то же при обновлении.
27. test_create_inventory_with_too_many_digits — проверяется допустимая общая точность quantity.
28. test_update_inventory_with_too_many_digits — то же при обновлении.

# 5. Tracked Product — 29 тестов
1. test_create_tracked_product — создание TrackedProduct.
2. test_create_tracked_product_with_default_minimum_quantity — работает значение minimum_quantity по умолчанию.
3. test_create_tracked_product_with_nonexistent_product — нельзя создать tracking для несуществующего Product.
4. test_create_duplicate_tracked_product — нельзя дважды отслеживать один Product в household.
5. test_create_tracked_product_with_zero_minimum_quantity — minimum_quantity = 0 разрешён.
6. test_create_tracked_product_with_negative_minimum_quantity — отрицательный minimum запрещён.
7. test_create_tracked_product_with_invalid_product_id — некорректный product_id отклоняется.
8. test_get_tracked_product — получение конкретного TrackedProduct.
9. test_get_tracked_products_empty — получение пустого списка tracking.
10. test_get_multiple_tracked_products — получение нескольких tracked products.
11. test_get_tracked_product_from_list_by_product_id — tracked product можно найти по product_id.
12. test_update_tracked_product — изменение tracked product.
13. test_update_tracked_product_with_zero_minimum_quantity — обновление minimum до 0.
14. test_update_tracked_product_with_negative_minimum_quantity — отрицательный minimum при обновлении запрещён.
15. test_update_nonexistent_tracked_product — обработка несуществующего tracked product.
16. test_delete_tracked_product — удаление tracked product.
17. test_delete_nonexistent_tracked_product — обработка удаления несуществующего tracked product.
18. test_user_cannot_access_another_household_tracked_products — нельзя получить tracking чужого household.
19. test_user_cannot_create_tracked_product_in_another_household — нельзя создать tracking в чужом household.
20. test_user_cannot_update_another_household_tracked_product — нельзя изменить чужой tracked product.
21. test_user_cannot_delete_another_household_tracked_product — нельзя удалить чужой tracked product.
22. test_get_low_stock_products — получение low-stock продуктов.
23. test_product_is_not_low_stock_when_quantity_is_above_minimum — количество выше minimum не считается low-stock.
24. test_product_is_low_stock_when_quantity_is_below_minimum — количество ниже minimum считается low-stock.
25. test_product_is_not_low_stock_when_quantity_equals_minimum — равенство minimum не считается low-stock.
26. test_low_stock_uses_zero_for_missing_inventory — отсутствие InventoryItem трактуется как количество 0.
27. test_low_stock_returns_only_low_products — в результат попадают только low-stock продукты.
28. test_user_cannot_access_low_stock_of_another_household — нельзя получить low-stock чужого household.