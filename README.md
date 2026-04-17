# Руководство по запуску и тестированию системы (Только для Windows)

Данное руководство содержит краткие и понятные инструкции по запуску сети Hyperledger Fabric и проверке функций чейнкода исключительно для операционной системы **Windows (PowerShell)**.

---

## 🚀 Часть 1: Подготовка и запуск сети

Все команды выполняются в терминале **PowerShell**, запущенном от имени администратора.

### 1. Подготовка окружения


Установите необходимые зависимости Python:
```powershell
pip install -r requirements.txt
```

Выполните очистку и генерацию сертификатов:
```powershell
# 1. Полная очистка старых данных (рекомендуется)
python network_setup.py clean

# 2. Генерация криптографических материалов (сертификатов)
python generate_crypto_materials.py

# 3. Запуск контейнеров блокчейн-сети
python network_setup.py start
```
*Подождите 20 секунд, пока Docker-контейнеры запустятся.*

### 2. Настройка канала и чейнкода
```powershell
# 1. Создание канала связи
python channel_setup.py

# 2. Запуск сервера чейнкода (в отдельном терминале или с флагом -d)
cd chaincode
docker compose -f docker-compose.chaincode.yaml up -d --build chaincode-server
cd ..

# 3. Регистрация чейнкода в сети
cd chaincode
python deploy_chaincode.py
cd ..
```

---

## 🛠 Часть 2: Тестирование функций (Windows)

Для надежной работы в Windows (PowerShell) мы используем метод копирования ключей администратора напрямую в контейнер. Это позволяет избежать проблем с сетевыми задержками и кавычками.

### 1. Подготовка прав Администратора
Выполните эти две команды один раз перед началом тестирования:
```powershell
# Копируем ключи администратора внутрь контейнера пира
docker exec peer0.org1.example.com mkdir -p /etc/hyperledger/fabric/admin-msp
docker cp ./organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp/. peer0.org1.example.com:/etc/hyperledger/fabric/admin-msp/
```

### 2. Запуск и проверка задач
Я обновил скрипт `invoke_within_peer.sh`, добавив в него удобные функции. Теперь вы можете легко создавать задачи, проверять их статус и историю.

#### А. Создание собственной задачи
1. Откройте файл `invoke_within_peer.sh` в редакторе.
2. В секции "А" раскомментируйте (уберите `#`) строку `invoke_task` и впишите свои данные.
3. Сохраните файл и выполните в PowerShell:
   ```powershell
   docker cp ./invoke_within_peer.sh peer0.org1.example.com:/tmp/invoke.sh
   docker exec peer0.org1.example.com /tmp/invoke.sh
   ```

#### Б. Проверка статуса (Query)
Чтобы увидеть текущий статус в «красивом» и читаемом виде:
1. Раскомментируйте строку в секции "Б" скрипта.
2. Выполните:
   ```powershell
   docker cp ./invoke_within_peer.sh peer0.org1.example.com:/tmp/invoke.sh
   docker exec peer0.org1.example.com /tmp/invoke.sh | ConvertFrom-Json | ConvertTo-Json -Depth 10
   ```

#### В. Просмотр истории (History)
Чтобы увидеть все изменения задачи (кто, когда и какой транзакцией менял данные):
1. Раскомментируйте строку в секции "В" скрипта.
2. Запустите ту же команду из пункта Б (через `ConvertTo-Json`).

### 3. Полезные советы для Windows
1.  **Русский язык**: Скрипт автоматически настраивает UTF-8, поэтому русский текст будет отображаться корректно.
2.  **Эндорсмент**: Скрипт сам запрашивает подписи у обоих организаций (Org1 и Org2). Вам не нужно ничего менять в командах.
3.  **Форматирование**: Команда `| ConvertFrom-Json | ConvertTo-Json` в PowerShell делает JSON-ответ от блокчейна человекочитаемым.
4.  **Логи чейнкода**: Если что-то не работает, проверьте логи сервера: `docker logs chaincode-server`.

---

## 📊 Автоматическая проверка
Для полной автоматизированной проверки всех функций проекта (History, Rich Query и т.д.) запустите:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force; .\verify_features.ps1
```
