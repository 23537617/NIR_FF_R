# IPFS Module

Модуль для работы с IPFS (InterPlanetary File System) на Python.

## Установка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Запуск IPFS ноды

Перед использованием модуля необходимо запустить IPFS ноду:

```bash
# Установка IPFS (если еще не установлен)
# Скачайте с https://ipfs.io/install/

# Инициализация IPFS (первый запуск)
ipfs init

# Запуск IPFS ноды
ipfs daemon
```

IPFS нода будет доступна по адресу: `http://127.0.0.1:5001`

## Использование

### Простые функции

```python
from ipfs_module import upload_document, download_document

# Загрузка файла в IPFS
result = upload_document("path/to/document.pdf")
if result["success"]:
    ipfs_hash = result["hash"]
    print(f"Файл загружен. Hash: {ipfs_hash}")

# Скачивание файла из IPFS
result = download_document(ipfs_hash, output_path="downloaded_file.pdf")
if result["success"]:
    print(f"Файл скачан: {result['path']}")
```

### Использование класса IPFSClient

```python
from ipfs_module import IPFSClient

# Создание клиента
client = IPFSClient(ipfs_host="/ip4/127.0.0.1/tcp/5001")

# Загрузка файла
result = client.upload_document("document.pdf", pin=True)
ipfs_hash = result["hash"]

# Получение информации о файле
info = client.get_file_info(ipfs_hash)

# Закрепление файла
client.pin_file(ipfs_hash)

# Скачивание файла
result = client.download_document(ipfs_hash, output_path="downloaded.pdf")

# Закрытие соединения
client.close()
```

## API

### `upload_document(path, ipfs_host="/ip4/127.0.0.1/tcp/5001", pin=True)`

Загружает документ в IPFS.

**Параметры:**
- `path` (str): Путь к файлу для загрузки
- `ipfs_host` (str): Адрес IPFS ноды
- `pin` (bool): Закрепить файл в IPFS (по умолчанию True)

**Возвращает:**
```python
{
    "success": True,
    "hash": "QmHash...",  # IPFS hash (CID)
    "size": 1024,         # Размер файла в байтах
    "path": "/path/to/file.pdf",
    "name": "file.pdf"
}
```

### `download_document(hash, output_path=None, ipfs_host="/ip4/127.0.0.1/tcp/5001")`

Скачивает документ из IPFS.

**Параметры:**
- `hash` (str): IPFS hash (CID) документа
- `output_path` (str, optional): Путь для сохранения файла
- `ipfs_host` (str): Адрес IPFS ноды

**Возвращает:**
```python
{
    "success": True,
    "path": "/path/to/downloaded/file.pdf",
    "hash": "QmHash...",
    "size": 1024
}
```

### `IPFSClient`

Класс для работы с IPFS.

#### Методы:

- `upload_document(path, pin=True)` - Загрузить документ
- `download_document(hash, output_path=None)` - Скачать документ
- `get_file_info(hash)` - Получить информацию о файле
- `pin_file(hash)` - Закрепить файл
- `unpin_file(hash)` - Открепить файл
- `close()` - Закрыть соединение

## Примеры

### Пример 1: Загрузка и скачивание

```python
from ipfs_module import upload_document, download_document

# Загрузка
result = upload_document("my_document.pdf")
if result["success"]:
    ipfs_hash = result["hash"]
    print(f"Hash: {ipfs_hash}")
    
    # Скачивание
    download_result = download_document(ipfs_hash, "downloaded.pdf")
    if download_result["success"]:
        print(f"Файл сохранен: {download_result['path']}")
```

### Пример 2: Работа с несколькими файлами

```python
from ipfs_module import IPFSClient

client = IPFSClient()

files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
hashes = []

for file in files:
    result = client.upload_document(file)
    if result["success"]:
        hashes.append(result["hash"])
        print(f"{file} -> {result['hash']}")

# Скачивание всех файлов
for i, hash in enumerate(hashes):
    client.download_document(hash, f"downloaded_{i}.pdf")

client.close()
```

### Пример 3: Интеграция с chaincode

```python
from ipfs_module import upload_document, download_document
from chaincode_client import ChaincodeClient

# Загрузка документа в IPFS
ipfs_result = upload_document("document.pdf")
if ipfs_result["success"]:
    ipfs_hash = ipfs_result["hash"]
    
    # Сохранение hash в chaincode
    chaincode_client = ChaincodeClient(...)
    chaincode_client.add_document_version(
        task_id="TASK001",
        document_id="DOC001",
        version="1.0",
        content_hash=ipfs_hash,  # Используем IPFS hash
        uploaded_by="user1"
    )
```

## Обработка ошибок

Все функции возвращают словарь с полем `success`:

```python
result = upload_document("file.pdf")

if result["success"]:
    # Успешная операция
    hash = result["hash"]
else:
    # Ошибка
    error = result["error"]
    print(f"Ошибка: {error}")
```

## Настройка

### Переменные окружения

```bash
# Адрес IPFS ноды
export IPFS_HOST="/ip4/127.0.0.1/tcp/5001"

# Или для удаленной ноды
export IPFS_HOST="/ip4/192.168.1.100/tcp/5001"
```

### Использование удаленной IPFS ноды

```python
from ipfs_module import IPFSClient

# Подключение к удаленной ноде
client = IPFSClient(ipfs_host="/ip4/192.168.1.100/tcp/5001")
```

## Требования

- Python 3.7+
- ipfshttpclient >= 0.8.0a2
- Запущенная IPFS нода

## Примечания

- Файлы, загруженные с `pin=True`, будут закреплены в IPFS и не будут удалены при очистке кеша
- Если `output_path` не указан при скачивании, файл сохраняется во временную директорию
- Убедитесь, что IPFS нода запущена перед использованием модуля



