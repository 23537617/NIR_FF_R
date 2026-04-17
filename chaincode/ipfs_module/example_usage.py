#!/usr/bin/env python3
"""
Примеры использования IPFS модуля
"""

import os
import json
from pathlib import Path
from ipfs_client import IPFSClient, upload_document, download_document


def example_upload():
    """Пример загрузки файла в IPFS"""
    print("\n=== Пример загрузки файла в IPFS ===")
    
    # Создаем тестовый файл
    test_file = Path("test_document.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("Это тестовый документ для загрузки в IPFS\n")
        f.write("Содержимое файла для проверки работы модуля.")
    
    print(f"Создан тестовый файл: {test_file}")
    
    # Загрузка файла
    result = upload_document(str(test_file))
    
    print(f"\nРезультат загрузки:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("success"):
        ipfs_hash = result.get("hash")
        print(f"\n✓ Файл успешно загружен!")
        print(f"  IPFS Hash: {ipfs_hash}")
        print(f"  Размер: {result.get('size')} bytes")
        return ipfs_hash
    
    return None


def example_download(ipfs_hash: str):
    """Пример скачивания файла из IPFS"""
    print(f"\n=== Пример скачивания файла из IPFS ===")
    print(f"Hash: {ipfs_hash}")
    
    # Скачивание файла
    result = download_document(ipfs_hash, output_path="downloaded_document.txt")
    
    print(f"\nРезультат скачивания:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("success"):
        file_path = result.get("path")
        print(f"\n✓ Файл успешно скачан!")
        print(f"  Путь: {file_path}")
        print(f"  Размер: {result.get('size')} bytes")
        
        # Показываем содержимое
        if Path(file_path).exists():
            print(f"\nСодержимое файла:")
            with open(file_path, "r", encoding="utf-8") as f:
                print(f.read())


def example_with_client():
    """Пример использования IPFSClient напрямую"""
    print("\n=== Пример использования IPFSClient ===")
    
    # Создание клиента
    client = IPFSClient()
    
    # Создаем тестовый файл
    test_file = Path("test_file2.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("Второй тестовый файл\n")
        f.write("Для демонстрации работы IPFSClient")
    
    # Загрузка
    upload_result = client.upload_document(str(test_file))
    print(f"Загрузка: {json.dumps(upload_result, indent=2, ensure_ascii=False)}")
    
    if upload_result.get("success"):
        ipfs_hash = upload_result.get("hash")
        
        # Получение информации о файле
        info = client.get_file_info(ipfs_hash)
        print(f"\nИнформация о файле: {json.dumps(info, indent=2, ensure_ascii=False)}")
        
        # Скачивание
        download_result = client.download_document(ipfs_hash, output_path="downloaded_file2.txt")
        print(f"\nСкачивание: {json.dumps(download_result, indent=2, ensure_ascii=False)}")
    
    # Закрытие соединения
    client.close()


def main():
    """Главная функция"""
    print("="*60)
    print("Примеры использования IPFS модуля")
    print("="*60)
    
    try:
        # Пример 1: Использование функций-оберток
        ipfs_hash = example_upload()
        
        if ipfs_hash:
            example_download(ipfs_hash)
        
        # Пример 2: Использование класса напрямую
        example_with_client()
        
        print("\n" + "="*60)
        print("✓ Все примеры выполнены успешно")
        print("="*60)
    
    except Exception as e:
        print(f"\n❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Очистка тестовых файлов
        test_files = ["test_document.txt", "test_file2.txt", 
                     "downloaded_document.txt", "downloaded_file2.txt"]
        for file in test_files:
            if Path(file).exists():
                os.remove(file)
                print(f"Удален тестовый файл: {file}")


if __name__ == "__main__":
    main()



