#!/usr/bin/env python3
"""
Скрипт для управления сетью Hyperledger Fabric
"""

import subprocess
import os
import sys
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Выполняет команду и выводит результат"""
    print(f"\n{'='*60}")
    print(f"Выполняется: {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Ошибка: {result.stderr}")
        if check:
            return False
    else:
        print(f"✓ Успешно")
        if result.stdout:
            print(result.stdout)
    return result.returncode == 0


def check_docker():
    """Проверяет наличие Docker"""
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        subprocess.run(["docker", "compose", "version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker или Docker Compose не найдены")
        return False


def check_files():
    """Проверяет наличие необходимых файлов"""
    base_dir = Path(__file__).parent
    required_files = [
        base_dir / "config" / "crypto-config.yaml",
        base_dir / "config" / "configtx.yaml",
        base_dir / "docker-compose.yaml"
    ]
    
    missing = []
    for file in required_files:
        if not file.exists():
            missing.append(str(file))
    
    if missing:
        print("❌ Отсутствуют необходимые файлы:")
        for f in missing:
            print(f"   - {f}")
        print("\nСначала запустите: python generate_fabric_config.py")
        return False
    
    return True


def start_network():
    """Запускает сеть"""
    base_dir = Path(__file__).parent
    
    if not check_docker():
        return False
    
    if not check_files():
        return False
    
    # Проверяем наличие артефактов
    genesis_block = base_dir / "channel-artifacts" / "genesis.block"
    if not genesis_block.exists():
        print("⚠️  Genesis блок не найден")
        print("   Сначала запустите: python generate_crypto_materials.py")
        response = input("   Продолжить все равно? (y/n): ")
        if response.lower() != 'y':
            return False
    
    print("\n🚀 Запуск сети Hyperledger Fabric...")
    return run_command(["docker", "compose", "up", "-d"], cwd=base_dir)


def stop_network():
    """Останавливает сеть"""
    base_dir = Path(__file__).parent
    print("\n🛑 Остановка сети...")
    return run_command(["docker", "compose", "down"], cwd=base_dir)


def stop_network_clean():
    """Останавливает сеть и удаляет volumes"""
    base_dir = Path(__file__).parent
    print("\n🛑 Остановка сети и очистка volumes...")
    return run_command(["docker", "compose", "down", "-v"], cwd=base_dir)


def show_status():
    """Показывает статус контейнеров"""
    base_dir = Path(__file__).parent
    print("\n📊 Статус контейнеров (все):")
    run_command(["docker", "compose", "ps", "-a"], cwd=base_dir, check=False)


def show_logs():
    """Показывает логи"""
    base_dir = Path(__file__).parent
    print("\n📋 Логи контейнеров:")
    run_command(["docker", "compose", "logs", "-f", "--tail=100"], cwd=base_dir, check=False)


def main():
    if len(sys.argv) < 2:
        print("""
Использование: python network_setup.py <команда>

Команды:
  start       - Запустить сеть
  stop        - Остановить сеть
  clean       - Остановить сеть и удалить volumes
  status      - Показать статус контейнеров
  logs        - Показать логи контейнеров
  help        - Показать эту справку
        """)
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        start_network()
    elif command == "stop":
        stop_network()
    elif command == "clean":
        stop_network_clean()
    elif command == "status":
        show_status()
    elif command == "logs":
        show_logs()
    elif command == "help":
        main()
    else:
        print(f"❌ Неизвестная команда: {command}")
        print("Используйте: python network_setup.py help")


if __name__ == "__main__":
    main()

