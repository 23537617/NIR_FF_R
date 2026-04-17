#!/usr/bin/env python3
"""
Fabric SDK Python клиент для работы с Hyperledger Fabric сетью
Подключается к сети через connection profile и вызывает функции chaincode
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

# Попытка импорта различных версий Fabric SDK
FABRIC_SDK_AVAILABLE = False
FABRIC_SDK_TYPE = None

try:
    # Попытка импорта fabric-sdk-py (hfc)
    from hfc.fabric import Client as FabricClient
    from hfc.fabric_network import Network
    FABRIC_SDK_AVAILABLE = True
    FABRIC_SDK_TYPE = "hfc"
    logger.info("Используется fabric-sdk-py (hfc)")
except ImportError:
    try:
        # Попытка импорта fabric-network (официальный SDK)
        from fabric_network import Gateway, Network
        FABRIC_SDK_AVAILABLE = True
        FABRIC_SDK_TYPE = "gateway"
        logger.info("Используется fabric-network (Gateway)")
    except ImportError:
        FABRIC_SDK_AVAILABLE = False
        FABRIC_SDK_TYPE = None
        logging.warning("Fabric SDK не установлен. Используется упрощенная версия клиента.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FabricClientWrapper:
    """
    Обертка для Fabric SDK клиента
    Упрощенная версия для работы без полного SDK
    """
    
    def __init__(self, connection_profile_path: str):
        """
        Инициализация клиента
        
        Args:
            connection_profile_path: Путь к файлу connection profile (connection-org1.json)
        """
        self.connection_profile_path = Path(connection_profile_path)
        self.connection_profile = self._load_connection_profile()
        self.client = None
        
        if FABRIC_SDK_AVAILABLE:
            self._init_fabric_client()
        else:
            logger.warning("Используется упрощенный режим без полного SDK")
    
    def _load_connection_profile(self) -> Dict[str, Any]:
        """Загрузить connection profile из JSON файла"""
        try:
            with open(self.connection_profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            logger.info(f"Connection profile загружен из {self.connection_profile_path}")
            return profile
        except FileNotFoundError:
            logger.error(f"Файл connection profile не найден: {self.connection_profile_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {str(e)}")
            raise
    
    def _init_fabric_client(self):
        """Инициализировать Fabric SDK клиент"""
        if not FABRIC_SDK_AVAILABLE:
            return
        
        try:
            if FABRIC_SDK_TYPE == "hfc":
                from hfc.fabric import Client as FabricClient
                self.client = FabricClient(net_profile=str(self.connection_profile_path))
            elif FABRIC_SDK_TYPE == "gateway":
                # Для Gateway SDK инициализация происходит по-другому
                self.client = None  # Gateway создается отдельно
            logger.info("Fabric SDK клиент инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации Fabric SDK клиента: {str(e)}")
            self.client = None
    
    def get_network(self, channel_name: str, user_name: str = "Admin", org_name: str = "Org1") -> Optional[Any]:
        """
        Получить объект сети
        
        Args:
            channel_name: Имя канала
            user_name: Имя пользователя
            org_name: Имя организации
        
        Returns:
            Объект Network или None
        """
        if not FABRIC_SDK_AVAILABLE:
            logger.error("Fabric SDK недоступен")
            return None
        
        try:
            if FABRIC_SDK_TYPE == "hfc" and self.client:
                org = self.client.get_org(org_name)
                user = org.get_user(user_name)
                network = self.client.get_network(channel_name, user)
                logger.info(f"Сеть {channel_name} получена для пользователя {user_name}")
                return network
            elif FABRIC_SDK_TYPE == "gateway":
                # Для Gateway SDK нужна отдельная инициализация
                logger.warning("Gateway SDK требует отдельной инициализации")
                return None
        except Exception as e:
            logger.error(f"Ошибка получения сети: {str(e)}")
            return None
        
        return None


class ChaincodeClient:
    """
    Клиент для вызова функций chaincode
    """
    
    def __init__(self, connection_profile_path: str, channel_name: str = "npa-channel",
                 chaincode_name: str = "taskdocument", org_name: str = "Org1", user_name: str = "Admin"):
        """
        Инициализация клиента chaincode
        
        Args:
            connection_profile_path: Путь к connection profile
            channel_name: Имя канала
            chaincode_name: Имя chaincode
            org_name: Имя организации
            user_name: Имя пользователя
        """
        self.connection_profile_path = connection_profile_path
        self.channel_name = channel_name
        self.chaincode_name = chaincode_name
        self.org_name = org_name
        self.user_name = user_name
        
        self.fabric_client = FabricClientWrapper(connection_profile_path)
        self.network = None
        
        if FABRIC_SDK_AVAILABLE:
            self.network = self.fabric_client.get_network(channel_name, user_name, org_name)
    
    def invoke_chaincode(self, function: str, args: List[str], 
                        peers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Вызвать функцию chaincode (транзакция)
        
        Args:
            function: Имя функции chaincode
            args: Список аргументов функции
            peers: Список peer'ов для вызова (опционально)
        
        Returns:
            Результат выполнения функции
        """
        if not FABRIC_SDK_AVAILABLE or not self.network:
            logger.error("Fabric SDK недоступен. Используйте упрощенный метод.")
            return self._invoke_simple(function, args)
        
        try:
            contract = self.network.get_contract(self.chaincode_name)
            result = contract.submit_transaction(function, *args)
            
            # Парсим результат
            if isinstance(result, bytes):
                result = result.decode('utf-8')
            
            try:
                result_dict = json.loads(result)
            except json.JSONDecodeError:
                result_dict = {"result": result}
            
            logger.info(f"Функция {function} успешно выполнена")
            return {
                "success": True,
                "data": result_dict
            }
        
        except Exception as e:
            logger.error(f"Ошибка при вызове функции {function}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def query_chaincode(self, function: str, args: List[str],
                       peers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Выполнить query к chaincode (чтение)
        
        Args:
            function: Имя функции chaincode
            args: Список аргументов функции
            peers: Список peer'ов для запроса (опционально)
        
        Returns:
            Результат выполнения функции
        """
        if not FABRIC_SDK_AVAILABLE or not self.network:
            logger.error("Fabric SDK недоступен. Используйте упрощенный метод.")
            return self._query_simple(function, args)
        
        try:
            contract = self.network.get_contract(self.chaincode_name)
            result = contract.evaluate_transaction(function, *args)
            
            # Парсим результат
            if isinstance(result, bytes):
                result = result.decode('utf-8')
            
            try:
                result_dict = json.loads(result)
            except json.JSONDecodeError:
                result_dict = {"result": result}
            
            logger.info(f"Query {function} успешно выполнен")
            return {
                "success": True,
                "data": result_dict
            }
        
        except Exception as e:
            logger.error(f"Ошибка при выполнении query {function}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _invoke_simple(self, function: str, args: List[str]) -> Dict[str, Any]:
        """
        Упрощенный метод вызова chaincode (для случаев без SDK)
        Использует прямые команды peer через subprocess
        """
        logger.warning("Используется упрощенный метод вызова через peer CLI")
        # Здесь можно реализовать вызов через subprocess и команды peer
        return {
            "success": False,
            "error": "Требуется установка fabric-sdk-py для полной функциональности"
        }
    
    def _query_simple(self, function: str, args: List[str]) -> Dict[str, Any]:
        """
        Упрощенный метод query chaincode (для случаев без SDK)
        """
        logger.warning("Используется упрощенный метод query через peer CLI")
        return {
            "success": False,
            "error": "Требуется установка fabric-sdk-py для полной функциональности"
        }
    
    # Методы для работы с задачами
    def create_task(self, task_id: str, title: str, description: str,
                   assignee: str, creator: str) -> Dict[str, Any]:
        """Создать задачу"""
        return self.invoke_chaincode("createTask", [task_id, title, description, assignee, creator])
    
    def update_task_status(self, task_id: str, new_status: str, updated_by: str) -> Dict[str, Any]:
        """Обновить статус задачи"""
        return self.invoke_chaincode("updateTaskStatus", [task_id, new_status, updated_by])
    
    def add_document_version(self, task_id: str, document_id: str, version: str,
                            content_hash: str, uploaded_by: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Добавить версию документа"""
        args = [task_id, document_id, version, content_hash, uploaded_by]
        if metadata:
            args.append(json.dumps(metadata))
        return self.invoke_chaincode("addDocumentVersion", args)
    
    def get_document_versions(self, task_id: str, document_id: str) -> Dict[str, Any]:
        """Получить версии документа"""
        return self.query_chaincode("getDocumentVersions", [task_id, document_id])
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Получить задачу"""
        return self.query_chaincode("getTask", [task_id])


def main():
    """Пример использования клиента"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fabric Chaincode Client")
    parser.add_argument("--connection", default="connection-org1.json",
                       help="Путь к connection profile")
    parser.add_argument("--channel", default="npa-channel",
                       help="Имя канала")
    parser.add_argument("--chaincode", default="taskdocument",
                       help="Имя chaincode")
    parser.add_argument("--org", default="Org1",
                       help="Имя организации")
    parser.add_argument("--user", default="Admin",
                       help="Имя пользователя")
    
    args = parser.parse_args()
    
    # Инициализация клиента
    client = ChaincodeClient(
        connection_profile_path=args.connection,
        channel_name=args.channel,
        chaincode_name=args.chaincode,
        org_name=args.org,
        user_name=args.user
    )
    
    # Примеры использования
    print("\n=== Примеры использования клиента ===\n")
    
    # 1. Создание задачи
    print("1. Создание задачи...")
    result = client.create_task(
        task_id="TASK001",
        title="Тестовая задача",
        description="Описание тестовой задачи",
        assignee="user1",
        creator="admin"
    )
    print(f"Результат: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 2. Получение задачи
    print("\n2. Получение задачи...")
    result = client.get_task("TASK001")
    print(f"Результат: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 3. Обновление статуса
    print("\n3. Обновление статуса задачи...")
    result = client.update_task_status("TASK001", "IN_PROGRESS", "user1")
    print(f"Результат: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 4. Добавление версии документа
    print("\n4. Добавление версии документа...")
    result = client.add_document_version(
        task_id="TASK001",
        document_id="DOC001",
        version="1.0",
        content_hash="abc123def456",
        uploaded_by="user1",
        metadata={"filename": "test.pdf", "size": 1024}
    )
    print(f"Результат: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 5. Получение версий документа
    print("\n5. Получение версий документа...")
    result = client.get_document_versions("TASK001", "DOC001")
    print(f"Результат: {json.dumps(result, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    main()

