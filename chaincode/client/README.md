# Fabric SDK Python Client

Python клиент для работы с Hyperledger Fabric сетью через connection profile.

## Установка

```bash
cd chaincode/client
pip install -r requirements.txt
```

## Структура

```
client/
├── client.py              # Основной клиент для работы с Fabric
├── connection-org1.json   # Connection profile для Org1
├── requirements.txt       # Зависимости
└── README.md             # Документация
```

## Использование

### Базовое использование

```python
from client import ChaincodeClient

# Инициализация клиента
client = ChaincodeClient(
    connection_profile_path="connection-org1.json",
    channel_name="npa-channel",
    chaincode_name="taskdocument",
    org_name="Org1",
    user_name="Admin"
)

# Создание задачи
result = client.create_task(
    task_id="TASK001",
    title="Новая задача",
    description="Описание задачи",
    assignee="user1",
    creator="admin"
)

# Получение задачи
task = client.get_task("TASK001")

# Обновление статуса
client.update_task_status("TASK001", "IN_PROGRESS", "user1")

# Добавление версии документа
client.add_document_version(
    task_id="TASK001",
    document_id="DOC001",
    version="1.0",
    content_hash="abc123",
    uploaded_by="user1",
    metadata={"filename": "doc.pdf"}
)

# Получение версий документа
versions = client.get_document_versions("TASK001", "DOC001")
```

### Прямой вызов функций chaincode

```python
# Invoke (транзакция)
result = client.invoke_chaincode("createTask", [
    "TASK001", "Задача", "Описание", "user1", "admin"
])

# Query (чтение)
result = client.query_chaincode("getTask", ["TASK001"])
```

## Connection Profile

Файл `connection-org1.json` содержит конфигурацию для подключения к сети Fabric:

- **organizations**: Конфигурация организаций
- **orderers**: Конфигурация orderer'ов
- **peers**: Конфигурация peer'ов
- **channels**: Конфигурация каналов
- **certificateAuthorities**: Конфигурация CA серверов

### Настройка путей

Убедитесь, что пути к сертификатам в connection profile корректны относительно расположения файла:

```json
{
  "tlsCACerts": {
    "path": "../organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"
  }
}
```

## Запуск примера

```bash
python client.py --connection connection-org1.json --channel npa-channel
```

## API методов

### ChaincodeClient

#### `create_task(task_id, title, description, assignee, creator)`
Создает новую задачу.

#### `update_task_status(task_id, new_status, updated_by)`
Обновляет статус задачи.

#### `add_document_version(task_id, document_id, version, content_hash, uploaded_by, metadata=None)`
Добавляет версию документа к задаче.

#### `get_document_versions(task_id, document_id)`
Получает все версии документа.

#### `get_task(task_id)`
Получает задачу по ID.

#### `invoke_chaincode(function, args, peers=None)`
Вызывает функцию chaincode (транзакция).

#### `query_chaincode(function, args, peers=None)`
Выполняет query к chaincode (чтение).

## Примечания

- Для работы требуется установленный `fabric-sdk-py`
- Убедитесь, что сеть Fabric запущена и доступна
- Проверьте корректность путей к сертификатам в connection profile
- Для production использования настройте TLS и аутентификацию



