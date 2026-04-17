#!/usr/bin/env python3
"""
Зависимости FastAPI
Инициализация и управление Fabric клиентом
"""

import os
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

# Добавляем путь к клиенту
import sys
client_path = Path(__file__).parent.parent / "client"
if str(client_path) not in sys.path:
    sys.path.insert(0, str(client_path))

try:
    # Пробуем импортировать из client директории
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from client.client import ChaincodeClient
    CLIENT_AVAILABLE = True
except ImportError:
    try:
        # Альтернативный путь
        from client import ChaincodeClient
        CLIENT_AVAILABLE = True
    except ImportError:
        CLIENT_AVAILABLE = False
        logging.warning("Fabric клиент не найден. Убедитесь, что путь к client.py корректен.")

logger = logging.getLogger(__name__)

# Глобальный экземпляр клиента
_chaincode_client: Optional[ChaincodeClient] = None


@lru_cache()
def get_chaincode_client() -> ChaincodeClient:
    """
    Получить экземпляр Fabric chaincode клиента (singleton)
    
    Returns:
        ChaincodeClient экземпляр
    """
    global _chaincode_client
    
    if _chaincode_client is not None:
        return _chaincode_client
    
    if not CLIENT_AVAILABLE:
        raise RuntimeError(
            "Fabric клиент недоступен. "
            "Убедитесь, что client.py находится в правильной директории."
        )
    
    # Получение конфигурации из переменных окружения
    connection_profile = os.getenv(
        "FABRIC_CONNECTION_PROFILE",
        str(Path(__file__).parent.parent / "client" / "connection-org1.json")
    )
    
    channel_name = os.getenv("FABRIC_CHANNEL", "npa-channel")
    chaincode_name = os.getenv("FABRIC_CHAINCODE", "taskdocument")
    org_name = os.getenv("FABRIC_ORG", "Org1")
    user_name = os.getenv("FABRIC_USER", "Admin")
    
    try:
        _chaincode_client = ChaincodeClient(
            connection_profile_path=connection_profile,
            channel_name=channel_name,
            chaincode_name=chaincode_name,
            org_name=org_name,
            user_name=user_name
        )
        logger.info("Fabric chaincode клиент успешно инициализирован")
        return _chaincode_client
    
    except Exception as e:
        logger.error(f"Ошибка инициализации Fabric клиента: {str(e)}")
        raise RuntimeError(f"Не удалось инициализировать Fabric клиент: {str(e)}")


def reset_client():
    """Сбросить клиент (для тестирования)"""
    global _chaincode_client
    _chaincode_client = None
    get_chaincode_client.cache_clear()

