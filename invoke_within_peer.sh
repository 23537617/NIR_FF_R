#!/bin/bash
# Вспомогательный скрипт для запуска команд внутри peer-контейнера на Windows

export CORE_PEER_LOCALMSPID=Org1MSP
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/admin-msp

ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem
PEER0_ORG1_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/org1-tls-ca.crt
PEER0_ORG2_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/org2-tls-ca.crt

export LANG=C.UTF-8

# Функция для вызова (Invoke)
function invoke_task() {
    peer chaincode invoke -o orderer.example.com:7050 --waitForEvent --ordererTLSHostnameOverride orderer.example.com \
        --tls --cafile $ORDERER_CA -C npa-channel -n taskdocument \
        --peerAddresses peer0.org1.example.com:7051 --tlsRootCertFiles $PEER0_ORG1_CA \
        --peerAddresses peer0.org2.example.com:9051 --tlsRootCertFiles $PEER0_ORG2_CA \
        --certfile /etc/hyperledger/fabric/tls/server.crt --keyfile /etc/hyperledger/fabric/tls/server.key \
        -c "$1"
}

# Функция для запроса (Query)
function query_task() {
    # Подавляем логи stderr, чтобы видеть только чистый JSON результат
    peer chaincode query -C npa-channel -n taskdocument -c "$1" 2>/dev/null
}

# =========================================================================
# --- СЕКЦИЯ ДЛЯ ВАШИХ ТЕСТОВ (РАСКОММЕНТИРУЙТЕ НУЖНЫЙ) ---
# (Для теста Events (пункт 5) добавьте флаг --waitForEvent в функцию invoke_task на 18 строке)
# =========================================================================

# --- ТЕСТ 1: Client Identity (Идентификация клиента) ---
# 1.1 Создаем:
# invoke_task '{"function":"create_task","Args":["TASK_ID_1", "Тест идентификации", "Смотрим профиль", "Ivanov", "Admin"]}'
# 1.2 Смотрим поле creator:
#query_task '{"function":"get_task","Args":["TASK_ID_1"]}'

# --- ТЕСТ 2: History API (История изменений) ---
# 2.1 Создаем и дважды меняем:
# invoke_task '{"function":"create_task","Args":["TASK_HIST_1", "История", "Тест истории", "Petrov", "Admin"]}'
# invoke_task '{"function":"update_task_status","Args":["TASK_HIST_1", "IN_PROGRESS", "Petrov"]}'
# invoke_task '{"function":"update_task_status","Args":["TASK_HIST_1", "COMPLETED", "Petrov"]}'
# 2.2 Читаем историю (должно прийти 3 состояния):
# query_task '{"function":"get_task_history","Args":["TASK_HIST_1"]}'

# --- ТЕСТ 3: Rich Query (Сложные запросы CouchDB) ---
# 3.1 Создаем разные задачи (создайте все три за раз):
# invoke_task '{"function":"create_task","Args":["TASK_RQ_1", "Запрос 1", "Тест", "Ivanov", "Admin"]}'
# invoke_task '{"function":"create_task","Args":["TASK_RQ_2", "Запрос 2", "Тест", "Ivanov", "Admin"]}'
# invoke_task '{"function":"create_task","Args":["TASK_RQ_3", "Запрос 3", "Тест", "Petrov", "Admin"]}'
# 3.2 Ищем ТОЛЬКО задачи Иванова (Петрова быть не должно):
# query_task '{"function":"query_tasks","Args":["{\"selector\":{\"assignee\":\"Ivanov\"}}", "10", ""]}'

# --- ТЕСТ 4: Pagination (Пагинация выборок CouchDB) ---
# 4.1 Создаем 4 тестовые записи (создайте все 4 за раз):
# invoke_task '{"function":"create_task","Args":["TASK_PAGE_1", "P1", "D", "Sidorov", "Admin"]}'
# invoke_task '{"function":"create_task","Args":["TASK_PAGE_2", "P2", "D", "Sidorov", "Admin"]}'
# invoke_task '{"function":"create_task","Args":["TASK_PAGE_3", "P3", "D", "Sidorov", "Admin"]}'
#invoke_task '{"function":"create_task","Args":["TASK_PAGE_4", "P4", "D", "Sidorov", "Admin"]}'
# 4.2 Получаем ТОЛЬКО первые 2 записи (скопируйте отсюда закладку bookmark):
# query_task '{"function":"query_tasks","Args":["{\"selector\":{\"assignee\":\"Sidorov\"}}", "2", ""]}'
# 4.3 Вставьте ваш bookmark вместо "ВАША_ЗАКЛАДКА", чтобы получить остальные 2:
# query_task '{"function":"query_tasks","Args":["{\"selector\":{\"assignee\":\"Sidorov\"}}", "2", "ВАША_ЗАКЛАДКА"]}'

# --- ТЕСТ 5: Events (Блокчейн-события) ---
# 5.1 Создаем задачу и смотрим события:
# invoke_task '{"function":"create_task","Args":["TASK_EVENT_1", "Событие", "Тест", "Ivanov", "Admin"]}'

# --- ДОПОЛНИТЕЛЬНО: Посмотреть ВООБЩЕ ВСЕ задачи в базе ---
# query_task '{"function":"query_tasks","Args":["{\"selector\":{\"docType\":\"task\"}}", "100", ""]}'

# --- ТЕСТ 6: State Machine (Конечный автомат статусов) ---
# 6.1 Создаем:
# invoke_task '{"function":"create_task","Args":["TASK_STATE_1", "State", "Тест", "Ivanov", "Admin"]}'
# 6.2 Пытаемся прыгнуть из NEW сразу в CLOSED (должна быть ошибка!):
# invoke_task '{"function":"update_task_status","Args":["TASK_STATE_1", "CLOSED", "Ivanov"]}'
# 6.3 Переводим по правилам в IN_PROGRESS:
# invoke_task '{"function":"update_task_status","Args":["TASK_STATE_1", "IN_PROGRESS", "Ivanov"]}'

# --- ТЕСТ 7 & 8: Consensus и RBAC (Одобрение и закрытие) ---
# 7.1 Переводим задачу в статус REVIEW:
# invoke_task '{"function":"update_task_status","Args":["TASK_STATE_1", "REVIEW", "Ivanov"]}'
# 7.2 Пытаемся закрыть задачу БЕЗ консенсуса:
# invoke_task '{"function":"update_task_status","Args":["TASK_STATE_1", "CLOSED", "Ivanov"]}'
# 7.3 Добавляем подпись от Org1:
# invoke_task '{"function":"approve_task","Args":["TASK_STATE_1"]}'
# ==============================================================
# ВАЖНО ДЛЯ 7.4 и 8.1: Вы должны изменить хедер этого скрипта:
# export CORE_PEER_LOCALMSPID=Org2MSP
# export CORE_PEER_ADDRESS=peer0.org2.example.com:9051
# А также запускать на peer0.org2.example.com
# ==============================================================
# 7.4 Подпись Org2 (если скрипт перенастроен):
#invoke_task '{"function":"approve_task","Args":["TASK_STATE_1"]}'
# 8.1 Теперь закрываем задачу (если вы Администратор из Org2):
# invoke_task '{"function":"update_task_status","Args":["TASK_STATE_1", "CLOSED", "AdminOrg2"]}'