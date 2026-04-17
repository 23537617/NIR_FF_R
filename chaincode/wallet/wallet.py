#!/usr/bin/env python3
"""
Fabric Wallet Module
Модуль для создания и управления Fabric identity в локальном wallet
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logging.warning("cryptography не установлен. Установите: pip install cryptography")

try:
    from fabric_network import Wallet, X509Identity
    FABRIC_NETWORK_AVAILABLE = True
except ImportError:
    FABRIC_NETWORK_AVAILABLE = False
    logging.warning("fabric-network не установлен. Используется упрощенная реализация wallet.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FabricWallet:
    """
    Класс для работы с Fabric wallet (локальное хранилище identity)
    
    Управляет созданием, хранением и получением Fabric identity
    """
    
    def __init__(self, wallet_path: str = "./wallet"):
        """
        Инициализация wallet
        
        Args:
            wallet_path: Путь к директории wallet
        """
        self.wallet_path = Path(wallet_path)
        self.wallet_path.mkdir(parents=True, exist_ok=True)
        
        # Используем fabric-network Wallet если доступен
        if FABRIC_NETWORK_AVAILABLE:
            try:
                self.wallet = Wallet(str(self.wallet_path))
                logger.info(f"Используется fabric-network Wallet: {self.wallet_path}")
            except Exception as e:
                logger.warning(f"Не удалось инициализировать fabric-network Wallet: {str(e)}")
                self.wallet = None
        else:
            self.wallet = None
        
        logger.info(f"Wallet инициализирован: {self.wallet_path}")
    
    def _get_identity_path(self, name: str) -> Path:
        """Получить путь к директории identity"""
        return self.wallet_path / name
    
    def _load_certificate_from_file(self, cert_path: Path) -> Optional[str]:
        """Загрузить сертификат из файла"""
        try:
            if cert_path.exists():
                with open(cert_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Ошибка загрузки сертификата: {str(e)}")
        return None
    
    def _load_private_key_from_file(self, key_path: Path) -> Optional[str]:
        """Загрузить приватный ключ из файла"""
        try:
            if key_path.exists():
                with open(key_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Ошибка загрузки приватного ключа: {str(e)}")
        return None
    
    def _load_identity_metadata(self, identity_path: Path) -> Dict[str, Any]:
        """Загрузить метаданные identity"""
        metadata_path = identity_path / "id.json"
        try:
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки метаданных: {str(e)}")
        return {}
    
    def _save_identity_metadata(self, identity_path: Path, name: str, role: str, 
                                msp_id: str = "Org1MSP"):
        """Сохранить метаданные identity"""
        metadata = {
            "name": name,
            "role": role,
            "msp_id": msp_id,
            "created_at": datetime.utcnow().isoformat(),
            "type": "X.509"
        }
        
        metadata_path = identity_path / "id.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def _create_identity_from_certs(self, name: str, role: str, 
                                   certificate: str, private_key: str,
                                   msp_id: str = "Org1MSP") -> Dict[str, Any]:
        """
        Создать identity из существующих сертификата и ключа
        
        Args:
            name: Имя identity
            role: Роль пользователя (admin, peer, client, user)
            certificate: Сертификат в формате PEM
            private_key: Приватный ключ в формате PEM
            msp_id: MSP ID организации
        
        Returns:
            Результат создания identity
        """
        try:
            identity_path = self._get_identity_path(name)
            identity_path.mkdir(parents=True, exist_ok=True)
            
            # Сохранение сертификата
            cert_path = identity_path / "certificate.pem"
            with open(cert_path, 'w', encoding='utf-8') as f:
                f.write(certificate)
            
            # Сохранение приватного ключа
            key_path = identity_path / "private_key.pem"
            with open(key_path, 'w', encoding='utf-8') as f:
                f.write(private_key)
            
            # Сохранение метаданных
            self._save_identity_metadata(identity_path, name, role, msp_id)
            
            logger.info(f"Identity '{name}' успешно создана")
            
            return {
                "success": True,
                "name": name,
                "role": role,
                "msp_id": msp_id,
                "path": str(identity_path)
            }
        
        except Exception as e:
            logger.error(f"Ошибка при создании identity: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_identity(self, name: str, role: str = "client", 
                       certificate: Optional[str] = None,
                       private_key: Optional[str] = None,
                       msp_id: str = "Org1MSP") -> Dict[str, Any]:
        """
        Создать Fabric identity для пользователя
        
        Args:
            name: Имя identity (уникальный идентификатор)
            role: Роль пользователя (admin, peer, client, user)
            certificate: Сертификат в формате PEM (опционально, если не указан - создается тестовый)
            private_key: Приватный ключ в формате PEM (опционально, если не указан - создается тестовый)
            msp_id: MSP ID организации
        
        Returns:
            Словарь с результатом создания identity
        """
        try:
            # Проверка существования identity
            if self.get_identity(name).get("success"):
                return {
                    "success": False,
                    "error": f"Identity с именем '{name}' уже существует"
                }
            
            # Если используется fabric-network Wallet
            if self.wallet and FABRIC_NETWORK_AVAILABLE:
                try:
                    # Если сертификат и ключ не предоставлены, создаем тестовые
                    if not certificate or not private_key:
                        # Для тестовых целей создаем простой identity
                        # В production используйте реальные сертификаты из CA
                        logger.warning("Создание identity без сертификата. Используйте реальные сертификаты из Fabric CA.")
                        return {
                            "success": False,
                            "error": "Для создания identity требуется сертификат и приватный ключ. Используйте Fabric CA для их получения."
                        }
                    
                    # Создание identity через fabric-network
                    identity = X509Identity(msp_id, certificate, private_key)
                    self.wallet.put(name, identity)
                    
                    logger.info(f"Identity '{name}' создана через fabric-network Wallet")
                    
                    return {
                        "success": True,
                        "name": name,
                        "role": role,
                        "msp_id": msp_id
                    }
                
                except Exception as e:
                    logger.warning(f"Ошибка создания через fabric-network Wallet: {str(e)}")
                    # Продолжаем с файловой системой
            
            # Создание через файловую систему
            if certificate and private_key:
                return self._create_identity_from_certs(name, role, certificate, private_key, msp_id)
            else:
                return {
                    "success": False,
                    "error": "Для создания identity требуется сертификат и приватный ключ. Используйте Fabric CA для их получения."
                }
        
        except Exception as e:
            logger.error(f"Ошибка при создании identity: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_identity(self, name: str) -> Dict[str, Any]:
        """
        Получить identity по имени
        
        Args:
            name: Имя identity
        
        Returns:
            Словарь с данными identity или ошибкой
        """
        try:
            identity_path = self._get_identity_path(name)
            
            if not identity_path.exists():
                return {
                    "success": False,
                    "error": f"Identity '{name}' не найдена"
                }
            
            # Загрузка сертификата и ключа
            cert_path = identity_path / "certificate.pem"
            key_path = identity_path / "private_key.pem"
            
            certificate = self._load_certificate_from_file(cert_path)
            private_key = self._load_private_key_from_file(key_path)
            metadata = self._load_identity_metadata(identity_path)
            
            if not certificate or not private_key:
                return {
                    "success": False,
                    "error": f"Неполные данные identity '{name}'"
                }
            
            return {
                "success": True,
                "name": name,
                "certificate": certificate,
                "private_key": private_key,
                "metadata": metadata,
                "path": str(identity_path)
            }
        
        except Exception as e:
            logger.error(f"Ошибка при получении identity: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_identities(self) -> List[Dict[str, Any]]:
        """
        Получить список всех identities в wallet
        
        Returns:
            Список словарей с информацией об identities
        """
        try:
            identities = []
            
            if not self.wallet_path.exists():
                return identities
            
            # Проходим по всем директориям в wallet
            for item in self.wallet_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    identity_name = item.name
                    
                    # Загружаем метаданные
                    metadata = self._load_identity_metadata(item)
                    
                    # Проверяем наличие сертификата
                    cert_path = item / "certificate.pem"
                    has_certificate = cert_path.exists()
                    
                    identities.append({
                        "name": identity_name,
                        "role": metadata.get("role", "unknown"),
                        "msp_id": metadata.get("msp_id", "unknown"),
                        "created_at": metadata.get("created_at", "unknown"),
                        "has_certificate": has_certificate,
                        "path": str(item)
                    })
            
            logger.info(f"Найдено {len(identities)} identities в wallet")
            return identities
        
        except Exception as e:
            logger.error(f"Ошибка при получении списка identities: {str(e)}")
            return []
    
    def delete_identity(self, name: str) -> Dict[str, Any]:
        """
        Удалить identity из wallet
        
        Args:
            name: Имя identity
        
        Returns:
            Результат удаления
        """
        try:
            identity_path = self._get_identity_path(name)
            
            if not identity_path.exists():
                return {
                    "success": False,
                    "error": f"Identity '{name}' не найдена"
                }
            
            # Удаление через fabric-network Wallet
            if self.wallet and FABRIC_NETWORK_AVAILABLE:
                try:
                    self.wallet.remove(name)
                except Exception:
                    pass  # Игнорируем ошибки, продолжаем с файловой системой
            
            # Удаление директории
            import shutil
            shutil.rmtree(identity_path)
            
            logger.info(f"Identity '{name}' удалена")
            
            return {
                "success": True,
                "message": f"Identity '{name}' успешно удалена"
            }
        
        except Exception as e:
            logger.error(f"Ошибка при удалении identity: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def export_identity(self, name: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Экспортировать identity в файл
        
        Args:
            name: Имя identity
            output_path: Путь для сохранения (опционально)
        
        Returns:
            Результат экспорта
        """
        try:
            identity_data = self.get_identity(name)
            
            if not identity_data.get("success"):
                return identity_data
            
            if not output_path:
                output_path = f"{name}_identity.json"
            
            export_data = {
                "name": name,
                "certificate": identity_data.get("certificate"),
                "private_key": identity_data.get("private_key"),
                "metadata": identity_data.get("metadata")
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Identity '{name}' экспортирована в {output_path}")
            
            return {
                "success": True,
                "path": output_path,
                "message": f"Identity экспортирована в {output_path}"
            }
        
        except Exception as e:
            logger.error(f"Ошибка при экспорте identity: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Глобальный экземпляр wallet (singleton)
_wallet_instance: Optional[FabricWallet] = None


def get_wallet(wallet_path: str = "./wallet") -> FabricWallet:
    """
    Получить глобальный экземпляр wallet
    
    Args:
        wallet_path: Путь к wallet
    
    Returns:
        FabricWallet экземпляр
    """
    global _wallet_instance
    
    if _wallet_instance is None:
        _wallet_instance = FabricWallet(wallet_path=wallet_path)
    
    return _wallet_instance


def create_identity(name: str, role: str = "client",
                   certificate: Optional[str] = None,
                   private_key: Optional[str] = None,
                   msp_id: str = "Org1MSP",
                   wallet_path: str = "./wallet") -> Dict[str, Any]:
    """
    Создать Fabric identity (удобная функция-обертка)
    
    Args:
        name: Имя identity
        role: Роль пользователя
        certificate: Сертификат в формате PEM
        private_key: Приватный ключ в формате PEM
        msp_id: MSP ID организации
        wallet_path: Путь к wallet
    
    Returns:
        Результат создания identity
    """
    wallet = get_wallet(wallet_path)
    return wallet.create_identity(name, role, certificate, private_key, msp_id)


def get_identity(name: str, wallet_path: str = "./wallet") -> Dict[str, Any]:
    """
    Получить identity по имени (удобная функция-обертка)
    
    Args:
        name: Имя identity
        wallet_path: Путь к wallet
    
    Returns:
        Данные identity
    """
    wallet = get_wallet(wallet_path)
    return wallet.get_identity(name)


def list_identities(wallet_path: str = "./wallet") -> List[Dict[str, Any]]:
    """
    Получить список всех identities (удобная функция-обертка)
    
    Args:
        wallet_path: Путь к wallet
    
    Returns:
        Список identities
    """
    wallet = get_wallet(wallet_path)
    return wallet.list_identities()



