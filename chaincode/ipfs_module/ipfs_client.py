#!/usr/bin/env python3
"""
IPFS Client Module
Модуль для работы с IPFS (InterPlanetary File System)
Использует библиотеку ipfshttpclient для загрузки и скачивания документов
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile

try:
    import ipfshttpclient
    IPFS_AVAILABLE = True
except ImportError:
    IPFS_AVAILABLE = False
    logging.warning("ipfshttpclient не установлен. Установите: pip install ipfshttpclient")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IPFSClient:
    """
    Клиент для работы с IPFS
    
    Предоставляет методы для загрузки и скачивания документов в/из IPFS
    """
    
    def __init__(self, ipfs_host: str = "/ip4/127.0.0.1/tcp/5001", 
                 ipfs_port: Optional[int] = None):
        """
        Инициализация IPFS клиента
        
        Args:
            ipfs_host: Адрес IPFS ноды (по умолчанию локальная нода)
            ipfs_port: Порт IPFS ноды (опционально, если указан в host)
        """
        self.ipfs_host = ipfs_host
        self.client = None
        
        if not IPFS_AVAILABLE:
            raise RuntimeError(
                "ipfshttpclient не установлен. "
                "Установите: pip install ipfshttpclient"
            )
        
        self._connect()
    
    def _connect(self):
        """Подключение к IPFS ноде"""
        try:
            # Формируем адрес подключения
            if self.ipfs_host.startswith("/"):
                connect_address = self.ipfs_host
            else:
                # Если передан обычный адрес, преобразуем
                connect_address = f"/ip4/{self.ipfs_host.replace('http://', '').replace('https://', '')}/tcp/5001"
            
            self.client = ipfshttpclient.connect(connect_address)
            logger.info(f"Подключение к IPFS ноде: {connect_address}")
            
            # Проверка подключения
            try:
                version = self.client.version()
                logger.info(f"IPFS версия: {version.get('Version', 'unknown')}")
            except Exception as e:
                logger.warning(f"Не удалось получить версию IPFS: {str(e)}")
        
        except ipfshttpclient.exceptions.ConnectionError as e:
            logger.error(f"Ошибка подключения к IPFS ноде: {str(e)}")
            raise RuntimeError(
                f"Не удалось подключиться к IPFS ноде по адресу {self.ipfs_host}. "
                "Убедитесь, что IPFS нода запущена."
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка при подключении к IPFS: {str(e)}")
            raise
    
    def upload_document(self, path: str, pin: bool = True) -> Dict[str, Any]:
        """
        Загрузить документ в IPFS
        
        Args:
            path: Путь к файлу для загрузки
            pin: Закрепить файл в IPFS (по умолчанию True)
        
        Returns:
            Словарь с результатом загрузки:
            {
                "success": bool,
                "hash": str,  # IPFS hash (CID)
                "size": int,  # Размер файла в байтах
                "path": str   # Путь к файлу
            }
        """
        try:
            file_path = Path(path)
            
            # Проверка существования файла
            if not file_path.exists():
                raise FileNotFoundError(f"Файл не найден: {path}")
            
            if not file_path.is_file():
                raise ValueError(f"Указанный путь не является файлом: {path}")
            
            logger.info(f"Загрузка файла в IPFS: {path}")
            
            # Загрузка файла в IPFS
            result = self.client.add(
                str(file_path),
                pin=pin,
                recursive=False
            )
            
            # Обработка результата
            if isinstance(result, list):
                # Если загружен один файл, берем первый элемент
                file_info = result[0]
            else:
                file_info = result
            
            ipfs_hash = file_info.get('Hash') or file_info.get('hash')
            file_size = file_info.get('Size', 0)
            
            if not ipfs_hash:
                raise ValueError("IPFS не вернул hash для загруженного файла")
            
            logger.info(f"Файл успешно загружен в IPFS. Hash: {ipfs_hash}, Size: {file_size} bytes")
            
            return {
                "success": True,
                "hash": ipfs_hash,
                "size": int(file_size) if file_size else 0,
                "path": str(file_path),
                "name": file_path.name
            }
        
        except FileNotFoundError as e:
            logger.error(f"Файл не найден: {str(e)}")
            return {
                "success": False,
                "error": f"Файл не найден: {str(e)}"
            }
        except ValueError as e:
            logger.error(f"Ошибка валидации: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except ipfshttpclient.exceptions.ConnectionError as e:
            logger.error(f"Ошибка подключения к IPFS: {str(e)}")
            return {
                "success": False,
                "error": f"Ошибка подключения к IPFS: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла в IPFS: {str(e)}")
            return {
                "success": False,
                "error": f"Ошибка загрузки: {str(e)}"
            }
    
    def download_document(self, hash: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Скачать документ из IPFS
        
        Args:
            hash: IPFS hash (CID) документа
            output_path: Путь для сохранения файла (опционально)
                        Если не указан, файл сохраняется во временную директорию
        
        Returns:
            Словарь с результатом скачивания:
            {
                "success": bool,
                "path": str,      # Путь к скачанному файлу
                "hash": str,       # IPFS hash
                "size": int        # Размер файла в байтах
            }
        """
        try:
            if not hash or not hash.strip():
                raise ValueError("IPFS hash не может быть пустым")
            
            hash = hash.strip()
            logger.info(f"Скачивание файла из IPFS. Hash: {hash}")
            
            # Определяем путь для сохранения
            if output_path:
                output_file = Path(output_path)
                output_dir = output_file.parent
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                # Используем временную директорию
                temp_dir = tempfile.gettempdir()
                output_file = Path(temp_dir) / f"ipfs_{hash}"
            
            # Скачивание файла из IPFS
            try:
                # Получаем файл из IPFS
                file_data = self.client.cat(hash)
                
                # Сохраняем файл
                with open(output_file, 'wb') as f:
                    f.write(file_data)
                
                file_size = output_file.stat().st_size
                
                logger.info(f"Файл успешно скачан из IPFS. Path: {output_file}, Size: {file_size} bytes")
                
                return {
                    "success": True,
                    "path": str(output_file),
                    "hash": hash,
                    "size": file_size
                }
            
            except ipfshttpclient.exceptions.ErrorResponse as e:
                if "not found" in str(e).lower() or "no link named" in str(e).lower():
                    logger.error(f"Файл не найден в IPFS: {hash}")
                    return {
                        "success": False,
                        "error": f"Файл с hash {hash} не найден в IPFS"
                    }
                else:
                    raise
        
        except ValueError as e:
            logger.error(f"Ошибка валидации: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except ipfshttpclient.exceptions.ConnectionError as e:
            logger.error(f"Ошибка подключения к IPFS: {str(e)}")
            return {
                "success": False,
                "error": f"Ошибка подключения к IPFS: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Ошибка при скачивании файла из IPFS: {str(e)}")
            return {
                "success": False,
                "error": f"Ошибка скачивания: {str(e)}"
            }
    
    def get_file_info(self, hash: str) -> Dict[str, Any]:
        """
        Получить информацию о файле в IPFS
        
        Args:
            hash: IPFS hash (CID) документа
        
        Returns:
            Словарь с информацией о файле
        """
        try:
            if not hash or not hash.strip():
                raise ValueError("IPFS hash не может быть пустым")
            
            hash = hash.strip()
            
            # Получаем статистику файла
            stat = self.client.files.stat(f"/ipfs/{hash}")
            
            return {
                "success": True,
                "hash": hash,
                "size": stat.get("Size", 0),
                "type": stat.get("Type", "unknown"),
                "cumulative_size": stat.get("CumulativeSize", 0)
            }
        
        except Exception as e:
            logger.error(f"Ошибка при получении информации о файле: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def pin_file(self, hash: str) -> Dict[str, Any]:
        """
        Закрепить файл в IPFS (предотвратить удаление)
        
        Args:
            hash: IPFS hash (CID) документа
        
        Returns:
            Результат операции
        """
        try:
            if not hash or not hash.strip():
                raise ValueError("IPFS hash не может быть пустым")
            
            hash = hash.strip()
            logger.info(f"Закрепление файла в IPFS: {hash}")
            
            self.client.pin.add(hash)
            
            return {
                "success": True,
                "hash": hash,
                "message": "Файл успешно закреплен"
            }
        
        except Exception as e:
            logger.error(f"Ошибка при закреплении файла: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def unpin_file(self, hash: str) -> Dict[str, Any]:
        """
        Открепить файл в IPFS
        
        Args:
            hash: IPFS hash (CID) документа
        
        Returns:
            Результат операции
        """
        try:
            if not hash or not hash.strip():
                raise ValueError("IPFS hash не может быть пустым")
            
            hash = hash.strip()
            logger.info(f"Открепление файла в IPFS: {hash}")
            
            self.client.pin.rm(hash)
            
            return {
                "success": True,
                "hash": hash,
                "message": "Файл успешно откреплен"
            }
        
        except Exception as e:
            logger.error(f"Ошибка при откреплении файла: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def close(self):
        """Закрыть соединение с IPFS"""
        if self.client:
            try:
                self.client.close()
                logger.info("Соединение с IPFS закрыто")
            except Exception as e:
                logger.warning(f"Ошибка при закрытии соединения: {str(e)}")


# Глобальный экземпляр клиента (singleton)
_ipfs_client: Optional[IPFSClient] = None


def get_ipfs_client(ipfs_host: str = "/ip4/127.0.0.1/tcp/5001") -> IPFSClient:
    """
    Получить глобальный экземпляр IPFS клиента
    
    Args:
        ipfs_host: Адрес IPFS ноды
    
    Returns:
        IPFSClient экземпляр
    """
    global _ipfs_client
    
    if _ipfs_client is None:
        _ipfs_client = IPFSClient(ipfs_host=ipfs_host)
    
    return _ipfs_client


def upload_document(path: str, ipfs_host: str = "/ip4/127.0.0.1/tcp/5001", 
                   pin: bool = True) -> Dict[str, Any]:
    """
    Загрузить документ в IPFS (удобная функция-обертка)
    
    Args:
        path: Путь к файлу для загрузки
        ipfs_host: Адрес IPFS ноды
        pin: Закрепить файл в IPFS
    
    Returns:
        Результат загрузки
    """
    client = get_ipfs_client(ipfs_host)
    return client.upload_document(path, pin=pin)


def download_document(hash: str, output_path: Optional[str] = None,
                     ipfs_host: str = "/ip4/127.0.0.1/tcp/5001") -> Dict[str, Any]:
    """
    Скачать документ из IPFS (удобная функция-обертка)
    
    Args:
        hash: IPFS hash (CID) документа
        output_path: Путь для сохранения файла
        ipfs_host: Адрес IPFS ноды
    
    Returns:
        Результат скачивания
    """
    client = get_ipfs_client(ipfs_host)
    return client.download_document(hash, output_path=output_path)



