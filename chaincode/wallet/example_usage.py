#!/usr/bin/env python3
"""
Примеры использования Fabric Wallet модуля
"""

import json
from pathlib import Path
from wallet import FabricWallet, create_identity, get_identity, list_identities


def example_create_identity():
    """Пример создания identity"""
    print("\n=== Пример создания identity ===")
    
    # Пример сертификата и ключа (в реальности получаются из Fabric CA)
    # Здесь используются примеры для демонстрации
    test_certificate = """-----BEGIN CERTIFICATE-----
MIICGjCCAcCgAwIBAgIRAKBZ... (пример сертификата)
-----END CERTIFICATE-----"""
    
    test_private_key = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg... (пример ключа)
-----END PRIVATE KEY-----"""
    
    # Создание wallet
    wallet = FabricWallet(wallet_path="./test_wallet")
    
    # Создание identity
    result = wallet.create_identity(
        name="user1",
        role="client",
        certificate=test_certificate,
        private_key=test_private_key,
        msp_id="Org1MSP"
    )
    
    print(f"Результат создания identity:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result.get("success")


def example_get_identity():
    """Пример получения identity"""
    print("\n=== Пример получения identity ===")
    
    wallet = FabricWallet(wallet_path="./test_wallet")
    
    # Получение identity
    result = wallet.get_identity("user1")
    
    if result.get("success"):
        print(f"Identity найдена:")
        print(f"  Имя: {result['name']}")
        print(f"  Роль: {result['metadata'].get('role', 'unknown')}")
        print(f"  MSP ID: {result['metadata'].get('msp_id', 'unknown')}")
        print(f"  Сертификат присутствует: {bool(result.get('certificate'))}")
        print(f"  Приватный ключ присутствует: {bool(result.get('private_key'))}")
    else:
        print(f"Ошибка: {result.get('error')}")


def example_list_identities():
    """Пример получения списка identities"""
    print("\n=== Пример получения списка identities ===")
    
    wallet = FabricWallet(wallet_path="./test_wallet")
    
    # Получение списка
    identities = wallet.list_identities()
    
    print(f"Найдено identities: {len(identities)}")
    for identity in identities:
        print(f"\n  Имя: {identity['name']}")
        print(f"  Роль: {identity['role']}")
        print(f"  MSP ID: {identity['msp_id']}")
        print(f"  Создано: {identity['created_at']}")
        print(f"  Сертификат: {'✓' if identity['has_certificate'] else '✗'}")


def example_with_functions():
    """Пример использования функций-оберток"""
    print("\n=== Пример использования функций-оберток ===")
    
    # Создание identity через функцию
    test_cert = "-----BEGIN CERTIFICATE-----\nTEST\n-----END CERTIFICATE-----"
    test_key = "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----"
    
    result = create_identity(
        name="user2",
        role="admin",
        certificate=test_cert,
        private_key=test_key,
        wallet_path="./test_wallet"
    )
    print(f"Создание через функцию: {result.get('success')}")
    
    # Получение identity через функцию
    identity = get_identity("user2", wallet_path="./test_wallet")
    print(f"Получение через функцию: {identity.get('success')}")
    
    # Список identities через функцию
    identities = list_identities(wallet_path="./test_wallet")
    print(f"Список через функцию: {len(identities)} identities")


def example_real_certificate():
    """Пример работы с реальными сертификатами из Fabric"""
    print("\n=== Пример работы с реальными сертификатами ===")
    
    # Путь к сертификатам из Fabric организаций
    org_cert_path = Path("../organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp/signcerts")
    org_key_path = Path("../organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp/keystore")
    
    if org_cert_path.exists() and org_key_path.exists():
        # Находим файлы сертификата и ключа
        cert_files = list(org_cert_path.glob("*.pem"))
        key_files = list(org_key_path.glob("*_sk"))
        
        if cert_files and key_files:
            # Загружаем сертификат
            with open(cert_files[0], 'r') as f:
                certificate = f.read()
            
            # Загружаем ключ
            with open(key_files[0], 'r') as f:
                private_key = f.read()
            
            # Создаем identity
            wallet = FabricWallet(wallet_path="./test_wallet")
            result = wallet.create_identity(
                name="admin_org1",
                role="admin",
                certificate=certificate,
                private_key=private_key,
                msp_id="Org1MSP"
            )
            
            print(f"Результат создания identity из реальных сертификатов:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Сертификаты не найдены в указанных путях")
    else:
        print("Пути к сертификатам не найдены. Убедитесь, что криптографические материалы сгенерированы.")


def main():
    """Главная функция"""
    print("="*60)
    print("Примеры использования Fabric Wallet")
    print("="*60)
    
    try:
        # Пример 1: Создание identity
        if example_create_identity():
            # Пример 2: Получение identity
            example_get_identity()
        
        # Пример 3: Список identities
        example_list_identities()
        
        # Пример 4: Использование функций-оберток
        example_with_functions()
        
        # Пример 5: Работа с реальными сертификатами
        example_real_certificate()
        
        print("\n" + "="*60)
        print("✓ Все примеры выполнены")
        print("="*60)
    
    except Exception as e:
        print(f"\n❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Очистка тестового wallet (опционально)
        import shutil
        test_wallet = Path("./test_wallet")
        if test_wallet.exists():
            response = input("\nУдалить тестовый wallet? (y/n): ")
            if response.lower() == 'y':
                shutil.rmtree(test_wallet)
                print("Тестовый wallet удален")


if __name__ == "__main__":
    main()



