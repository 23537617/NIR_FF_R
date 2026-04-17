#!/usr/bin/env python3
"""
Helper функции для работы с Fabric CA и сертификатами
Упрощает получение сертификатов для создания identity
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


def load_certificate_from_fabric_org(org_path: Path, user_name: str) -> Optional[Tuple[str, str]]:
    """
    Загрузить сертификат и ключ из сгенерированных Fabric материалов
    
    Args:
        org_path: Путь к директории организации (например, peerOrganizations/org1.example.com)
        user_name: Имя пользователя (например, Admin@org1.example.com)
    
    Returns:
        Кортеж (certificate, private_key) или None
    """
    try:
        # Путь к сертификату пользователя
        signcerts_path = org_path / "users" / user_name / "msp" / "signcerts"
        keystore_path = org_path / "users" / user_name / "msp" / "keystore"
        
        if not signcerts_path.exists() or not keystore_path.exists():
            logger.error(f"Пути к сертификатам не найдены для {user_name}")
            return None
        
        # Находим файл сертификата
        cert_files = list(signcerts_path.glob("*.pem"))
        if not cert_files:
            logger.error(f"Сертификат не найден в {signcerts_path}")
            return None
        
        # Находим файл приватного ключа
        key_files = list(keystore_path.glob("*_sk"))
        if not key_files:
            logger.error(f"Приватный ключ не найден в {keystore_path}")
            return None
        
        # Загружаем сертификат
        with open(cert_files[0], 'r', encoding='utf-8') as f:
            certificate = f.read()
        
        # Загружаем ключ
        with open(key_files[0], 'r', encoding='utf-8') as f:
            private_key = f.read()
        
        logger.info(f"Сертификаты загружены для {user_name}")
        return (certificate, private_key)
    
    except Exception as e:
        logger.error(f"Ошибка загрузки сертификатов: {str(e)}")
        return None


def create_identity_from_fabric_user(base_dir: str, org_domain: str, user_name: str,
                                    wallet_path: str = "./wallet",
                                    msp_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Создать identity из существующего пользователя Fabric
    
    Args:
        base_dir: Базовая директория (где находятся organizations/)
        org_domain: Домен организации (например, org1.example.com)
        user_name: Имя пользователя (например, Admin@org1.example.com)
        wallet_path: Путь к wallet
        msp_id: MSP ID (если не указан, определяется автоматически)
    
    Returns:
        Результат создания identity
    """
    from wallet import FabricWallet
    
    try:
        base_path = Path(base_dir)
        org_path = base_path / "organizations" / "peerOrganizations" / org_domain
        
        if not org_path.exists():
            return {
                "success": False,
                "error": f"Организация не найдена: {org_domain}"
            }
        
        # Определяем MSP ID если не указан
        if not msp_id:
            # Пытаемся определить из структуры
            org_name = org_domain.split('.')[0].capitalize()
            msp_id = f"{org_name}MSP"
        
        # Загружаем сертификаты
        cert_data = load_certificate_from_fabric_org(org_path, user_name)
        if not cert_data:
            return {
                "success": False,
                "error": f"Не удалось загрузить сертификаты для {user_name}"
            }
        
        certificate, private_key = cert_data
        
        # Определяем роль из имени пользователя
        role = "admin" if "admin" in user_name.lower() else "client"
        
        # Создаем identity
        wallet = FabricWallet(wallet_path=wallet_path)
        identity_name = user_name.replace('@', '_').replace('.', '_')
        
        result = wallet.create_identity(
            name=identity_name,
            role=role,
            certificate=certificate,
            private_key=private_key,
            msp_id=msp_id
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Ошибка создания identity из Fabric пользователя: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }



