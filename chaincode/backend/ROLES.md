# Система ролей и разрешений

## Роли пользователей

### юрист
**Разрешения:**
- ✅ Добавление версий документов (`add_document_version`)
- ✅ Просмотр задач (`view_task`)
- ✅ Просмотр документов (`view_documents`)

**Доступные endpoints:**
- `POST /document/addVersion`
- `GET /task/{task_id}`
- `GET /document/versions/{doc_id}`

### эксперт
**Разрешения:**
- ✅ Подтверждение задач (`confirm_task`)
- ✅ Просмотр задач (`view_task`)
- ✅ Просмотр документов (`view_documents`)

**Доступные endpoints:**
- `POST /task/confirm`
- `GET /task/{task_id}`
- `GET /document/versions/{doc_id}`

### модератор
**Разрешения:**
- ✅ Обновление статусов задач (`update_task_status`)
- ✅ Просмотр задач (`view_task`)
- ✅ Просмотр документов (`view_documents`)

**Доступные endpoints:**
- `POST /task/status/update`
- `GET /task/{task_id}`
- `GET /document/versions/{doc_id}`

### admin
**Разрешения:**
- ✅ Все разрешения (полный доступ)

**Доступные endpoints:**
- Все endpoints без ограничений

## Использование

### Указание роли в запросе

Роль указывается в HTTP заголовке `X-User-Role`:

```bash
curl -X POST "http://localhost:8000/document/addVersion" \
  -H "Content-Type: application/json" \
  -H "X-User-Role: юрист" \
  -d '{...}'
```

### Примеры для каждой роли

#### Юрист - добавление версии документа

```bash
curl -X POST "http://localhost:8000/document/addVersion" \
  -H "Content-Type: application/json" \
  -H "X-User-Role: юрист" \
  -d '{
    "task_id": "TASK001",
    "document_id": "DOC001",
    "version": "1.0",
    "content_hash": "abc123",
    "uploaded_by": "jurist1"
  }'
```

#### Эксперт - подтверждение задачи

```bash
curl -X POST "http://localhost:8000/task/confirm" \
  -H "Content-Type: application/json" \
  -H "X-User-Role: эксперт" \
  -d '{
    "task_id": "TASK001",
    "confirmed_by": "expert1",
    "comment": "Задача соответствует требованиям"
  }'
```

#### Модератор - обновление статуса

```bash
curl -X POST "http://localhost:8000/task/status/update" \
  -H "Content-Type: application/json" \
  -H "X-User-Role: модератор" \
  -d '{
    "task_id": "TASK001",
    "status": "IN_PROGRESS",
    "updated_by": "moderator1"
  }'
```

## Проверка разрешений

Для проверки текущих разрешений пользователя:

```bash
curl "http://localhost:8000/auth/user-info" \
  -H "X-User-Role: юрист"
```

Ответ:
```json
{
  "role": "юрист",
  "permissions": [
    "add_document_version",
    "view_task",
    "view_documents"
  ],
  "authenticated": true
}
```



