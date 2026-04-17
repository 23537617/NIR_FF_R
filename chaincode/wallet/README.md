# Fabric Wallet Module

Модуль для создания и управления Fabric identity в локальном wallet.

## Установка

```bash
pip install -r requirements.txt
```

## Использование

### Простые функции

```python
from wallet import create_identity, get_identity, list_identities

# Создание identity
result = create_identity(
    name="user1",
    role="client",
    certificate=certificate_pem,
    private_key=private_key_pem,
    msp_id="Org1MSP"
)

# Получение identity
identity = get_identity("user1")

# Список всех identities
identities = list_identities()
```

### Использование класса

```python
from wallet import FabricWallet

# Создание wallet
wallet = FabricWallet(wallet_path="./wallet")

# Создание identity
result = wallet.create_identity(
    name="user1",
    role="client",
    certificate=certificate_pem,
    private_key=private_key_pem
)

# Получение identity
identity = wallet.get_identity("user1")

# Список identities
identities = wallet.list_identities()

# Удаление identity
wallet.delete_identity("user1")
```

## API

### `create_identity(name, role="client", certificate=None, private_key=None, msp_id="Org1MSP", wallet_path="./wallet")`

Создает Fabric identity для пользователя.

**Параметры:**
- `name` (str): Имя identity (уникальный идентификатор)
- `role` (str): Роль пользователя (admin, peer, client, user)
- `certificate` (str): Сертификат в формате PEM
- `private_key` (str): Приватный ключ в формате PEM
- `msp_id` (str): MSP ID организации
- `wallet_path` (str): Путь к wallet директории

**Возвращает:**
```python
{
    "success": True,
    "name": "user1",
    "role": "client",
    "msp_id": "Org1MSP",
    "path": "./wallet/user1"
}
```

### `get_identity(name, wallet_path="./wallet")`

Получает identity по имени.

**Параметры:**
- `name` (str): Имя identity
- `wallet_path` (str): Путь к wallet директории

**Возвращает:**
```python
{
    "success": True,
    "name": "user1",
    "certificate": "-----BEGIN CERTIFICATE-----...",
    "private_key": "-----BEGIN PRIVATE KEY-----...",
    "metadata": {
        "name": "user1",
        "role": "client",
        "msp_id": "Org1MSP",
        "created_at": "2024-01-15T10:30:00Z"
    },
    "path": "./wallet/user1"
}
```

### `list_identities(wallet_path="./wallet")`

Получает список всех identities в wallet.

**Параметры:**
- `wallet_path` (str): Путь к wallet директории

**Возвращает:**
```python
[
    {
        "name": "user1",
        "role": "client",
        "msp_id": "Org1MSP",
        "created_at": "2024-01-15T10:30:00Z",
        "has_certificate": True,
        "path": "./wallet/user1"
    },
    ...
]
```

## Получение сертификатов из Fabric CA

Для создания identity нужны сертификат и приватный ключ. Их можно получить:

### Вариант 1: Из сгенерированных материалов

```python
from pathlib import Path

# Путь к сертификатам из cryptogen
cert_path = Path("../organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp/signcerts")
key_path = Path("../organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp/keystore")

# Загрузка сертификата
cert_files = list(cert_path.glob("*.pem"))
with open(cert_files[0], 'r') as f:
    certificate = f.read()

# Загрузка ключа
key_files = list(key_path.glob("*_sk"))
with open(key_files[0], 'r') as f:
    private_key = f.read()

# Создание identity
from wallet import create_identity
result = create_identity(
    name="admin_org1",
    role="admin",
    certificate=certificate,
    private_key=private_key,
    msp_id="Org1MSP"
)
```

### Вариант 2: Через Fabric CA

```python
# Используйте Fabric CA SDK для регистрации и получения сертификатов
# Затем создайте identity с полученными сертификатами
```

## Структура Wallet

Wallet хранится в файловой системе:

```
wallet/
├── user1/
│   ├── certificate.pem      # Сертификат
│   ├── private_key.pem      # Приватный ключ
│   └── id.json              # Метаданные
├── user2/
│   ├── certificate.pem
│   ├── private_key.pem
│   └── id.json
└── ...
```

## Интеграция с Fabric Client

```python
from wallet import get_identity
from client import ChaincodeClient

# Получение identity из wallet
identity_data = get_identity("user1")

if identity_data.get("success"):
    # Использование identity для подключения к Fabric
    # (в зависимости от используемого SDK)
    pass
```

## Примеры

### Пример 1: Создание и использование identity

```python
from wallet import create_identity, get_identity

# Создание identity
result = create_identity(
    name="developer1",
    role="client",
    certificate=cert_pem,
    private_key=key_pem
)

if result["success"]:
    # Получение identity
    identity = get_identity("developer1")
    print(f"Identity создана: {identity['name']}")
```

### Пример 2: Работа с несколькими identities

```python
from wallet import FabricWallet

wallet = FabricWallet()

# Создание нескольких identities
users = [
    {"name": "user1", "role": "client"},
    {"name": "user2", "role": "admin"},
    {"name": "user3", "role": "client"}
]

for user in users:
    wallet.create_identity(
        name=user["name"],
        role=user["role"],
        certificate=get_certificate_for_user(user["name"]),
        private_key=get_key_for_user(user["name"])
    )

# Список всех identities
identities = wallet.list_identities()
for identity in identities:
    print(f"{identity['name']} - {identity['role']}")
```

## Требования

- Python 3.7+
- cryptography >= 41.0.0
- fabric-network >= 1.0.0 (опционально, для расширенной функциональности)

## Примечания

- Сертификаты и ключи должны быть в формате PEM
- Identity хранятся локально в файловой системе
- Для production используйте реальные сертификаты из Fabric CA
- Wallet можно экспортировать/импортировать для переноса между системами



