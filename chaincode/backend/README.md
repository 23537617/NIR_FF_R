# FastAPI Backend для NPA Chaincode

REST API сервер для работы с Hyperledger Fabric chaincode через FastAPI.

## Установка

```bash
cd chaincode/backend
pip install -r requirements.txt
```

## Запуск

### Разработка

```bash
python main.py
```

Или через uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Авторизация и роли

API использует систему ролей для контроля доступа. Роль указывается в заголовке запроса:

```
X-User-Role: юрист
X-User-Role: эксперт
X-User-Role: модератор
X-User-Role: admin
```

### Роли и разрешения:

- **юрист** - может добавлять версии документов, просматривать задачи и документы
- **эксперт** - может подтверждать задачи, просматривать задачи и документы
- **модератор** - может обновлять статусы задач, просматривать задачи и документы
- **admin** - полный доступ ко всем операциям

## API Endpoints

### Health Check

- `GET /` - Информация о сервисе
- `GET /health` - Проверка работоспособности
- `GET /auth/user-info` - Информация о текущем пользователе и его разрешениях

### Tasks (Задачи)

#### `POST /task/create`
Создает новую задачу. **Требуется роль: admin**

**Headers:**
```
X-User-Role: admin
```

**Request Body:**
```json
{
  "task_id": "TASK001",
  "title": "Новая задача",
  "description": "Описание задачи",
  "assignee": "user1",
  "creator": "admin"
}
```

**Response:**
```json
{
  "success": true,
  "task": {
    "task_id": "TASK001",
    "title": "Новая задача",
    "status": "CREATED",
    ...
  },
  "message": "Задача успешно создана"
}
```

#### `POST /task/status/update`
Обновляет статус задачи. **Требуется роль: модератор**

**Headers:**
```
X-User-Role: модератор
```

**Request Body:**
```json
{
  "task_id": "TASK001",
  "status": "IN_PROGRESS",
  "updated_by": "user1"
}
```

**Допустимые статусы:** `CREATED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `CONFIRMED`

#### `POST /task/confirm`
Подтверждает задачу экспертом. **Требуется роль: эксперт**

**Headers:**
```
X-User-Role: эксперт
```

**Request Body:**
```json
{
  "task_id": "TASK001",
  "confirmed_by": "expert1",
  "comment": "Задача соответствует требованиям"
}
```

**Response:**
```json
{
  "success": true,
  "task": {
    "task_id": "TASK001",
    "status": "CONFIRMED",
    ...
  },
  "message": "Задача успешно подтверждена экспертом"
}
```

#### `GET /task/{task_id}`
Получает задачу по ID. **Требуется разрешение на просмотр задач**

**Headers:**
```
X-User-Role: юрист  # или эксперт, модератор, admin
```

**Response:**
```json
{
  "success": true,
  "task": {
    "task_id": "TASK001",
    "title": "Новая задача",
    ...
  },
  "message": "Задача успешно получена"
}
```

### Documents (Документы)

#### `POST /document/addVersion`
Добавляет версию документа к задаче. **Требуется роль: юрист**

**Headers:**
```
X-User-Role: юрист
```

**Request Body:**
```json
{
  "task_id": "TASK001",
  "document_id": "DOC001",
  "version": "1.0",
  "content_hash": "sha256:abc123...",
  "uploaded_by": "user1",
  "metadata": {
    "filename": "document.pdf",
    "size": 1024
  }
}
```

#### `GET /document/versions/{doc_id}?task_id={task_id}`
Получает все версии документа. **Требуется разрешение на просмотр документов**

**Headers:**
```
X-User-Role: юрист  # или эксперт, модератор, admin
```

**Query Parameters:**
- `task_id` (required) - Идентификатор задачи

**Response:**
```json
{
  "success": true,
  "task_id": "TASK001",
  "document_id": "DOC001",
  "versions": [
    {
      "version": "1.0",
      "content_hash": "sha256:abc123...",
      "uploaded_at": "2024-01-15T10:30:00Z",
      ...
    }
  ],
  "total_versions": 1,
  "message": "Версии документа успешно получены"
}
```

## Переменные окружения

```bash
# Путь к connection profile
export FABRIC_CONNECTION_PROFILE="../client/connection-org1.json"

# Имя канала
export FABRIC_CHANNEL="npa-channel"

# Имя chaincode
export FABRIC_CHAINCODE="taskdocument"

# Организация
export FABRIC_ORG="Org1"

# Пользователь
export FABRIC_USER="Admin"

# Порт API
export API_PORT=8000

# Хост API
export API_HOST="0.0.0.0"
```

## Документация API

После запуска сервера доступна автоматическая документация:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Примеры использования

### cURL

```bash
# Создание задачи (требуется роль admin)
curl -X POST "http://localhost:8000/task/create" \
  -H "Content-Type: application/json" \
  -H "X-User-Role: admin" \
  -d '{
    "task_id": "TASK001",
    "title": "Новая задача",
    "description": "Описание",
    "assignee": "user1",
    "creator": "admin"
  }'

# Обновление статуса (требуется роль модератор)
curl -X POST "http://localhost:8000/task/status/update" \
  -H "Content-Type: application/json" \
  -H "X-User-Role: модератор" \
  -d '{
    "task_id": "TASK001",
    "status": "IN_PROGRESS",
    "updated_by": "moderator1"
  }'

# Подтверждение задачи (требуется роль эксперт)
curl -X POST "http://localhost:8000/task/confirm" \
  -H "Content-Type: application/json" \
  -H "X-User-Role: эксперт" \
  -d '{
    "task_id": "TASK001",
    "confirmed_by": "expert1",
    "comment": "Задача соответствует требованиям"
  }'

# Добавление версии документа (требуется роль юрист)
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

# Получение версий документа (требуется разрешение на просмотр)
curl "http://localhost:8000/document/versions/DOC001?task_id=TASK001" \
  -H "X-User-Role: юрист"

# Получение задачи (требуется разрешение на просмотр)
curl "http://localhost:8000/task/TASK001" \
  -H "X-User-Role: юрист"
```

### Python

```python
import requests

# Создание задачи
response = requests.post("http://localhost:8000/task/create", json={
    "task_id": "TASK001",
    "title": "Новая задача",
    "description": "Описание",
    "assignee": "user1",
    "creator": "admin"
})
print(response.json())
```

## Структура проекта

```
backend/
├── main.py           # FastAPI приложение и маршруты
├── models.py         # Pydantic модели
├── dependencies.py   # Зависимости (Fabric клиент)
├── requirements.txt  # Зависимости Python
└── README.md        # Документация
```

## Обработка ошибок

API возвращает стандартизированные ответы об ошибках:

```json
{
  "success": false,
  "error": "Описание ошибки",
  "detail": "Детали ошибки"
}
```

HTTP статус коды:
- `200` - Успешный запрос
- `201` - Ресурс создан
- `400` - Ошибка валидации или бизнес-логики
- `404` - Ресурс не найден
- `500` - Внутренняя ошибка сервера

## Интеграция с Chaincode

Все маршруты автоматически вызывают соответствующие функции chaincode:

- `POST /task/create` → `createTask()` (admin)
- `POST /task/status/update` → `updateTaskStatus()` (модератор)
- `POST /task/confirm` → `updateTaskStatus()` со статусом CONFIRMED (эксперт)
- `POST /document/addVersion` → `addDocumentVersion()` (юрист)
- `GET /document/versions/{doc_id}` → `getDocumentVersions()` (все роли)
- `GET /task/{task_id}` → `getTask()` (все роли)

## Ошибки авторизации

При отсутствии необходимых прав API возвращает:

- `401 Unauthorized` - если роль не указана в заголовке `X-User-Role`
- `403 Forbidden` - если роль не имеет необходимых разрешений

Пример ошибки:
```json
{
  "detail": "Роль 'юрист' не имеет разрешения на выполнение этой операции. Требуется разрешение: update_task_status"
}
```

