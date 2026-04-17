#!/usr/bin/env python3
"""
Альтернативный скрипт для генерации криптографических материалов
Использует Docker образы Hyperledger Fabric для генерации
"""

import subprocess
import os
import platform
import sys
import shutil
from pathlib import Path
try:
    from generate_fabric_config import FabricConfigGenerator # type: ignore
except ImportError:
    class FabricConfigGenerator: # type: ignore
        def __init__(self, *args, **kwargs): pass
        def generate_config(self, *args, **kwargs): pass
        def generate_docker_compose(self, *args, **kwargs): pass
        def generate_all(self, *args, **kwargs): pass


class CryptoMaterialGenerator:
    def __init__(self, base_dir=".", platform_arch=None):
        self.base_dir = Path(base_dir).resolve()
        self.config_dir = self.base_dir / "config"
        self.orgs_dir = self.base_dir / "organizations"
        self.channel_dir = self.base_dir / "channel-artifacts"
        self.platform_arch = platform_arch or self.detect_platform()
        self.is_windows = sys.platform.startswith('win')
    
    def get_docker_path(self, path):
        """Конвертирует путь для Docker на Windows"""
        if self.is_windows:
            # Docker Desktop на Windows автоматически конвертирует пути,
            # но убедимся, что путь в правильном формате
            # Конвертируем обратные слэши в прямые
            docker_path = str(path).replace('\\', '/')
            # Если путь содержит двоеточие (диск Windows), Docker обычно справляется сам
            return docker_path
        return str(path)
    
    def detect_platform(self):
        """Определяет архитектуру платформы для Docker"""
        machine = platform.machine().lower()
        system = platform.system().lower()
        
        # Определение архитектуры
        if machine in ('x86_64', 'amd64', 'x64', 'i386', 'i686'):
            detected = "linux/amd64"
        elif machine in ('arm64', 'aarch64', 'armv8'):
            detected = "linux/arm64"
        elif machine.startswith('arm'):
            detected = "linux/arm64"  # Для ARM процессоров
        else:
            # По умолчанию используем amd64
            detected = "linux/amd64"
            print(f"⚠️  Неизвестная архитектура '{machine}', используется по умолчанию: {detected}")
        
        return detected
        
    def run_docker_command(self, cmd, description, timeout=300):
        """Выполняет команду через Docker"""
        print(f"\n{'='*60}")
        print(f"{description}")
        print(f"{'='*60}")
        print(f"Выполняется: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                print(f"❌ Ошибка: {result.stderr}")
                return False
            else:
                print(f"✓ Успешно: {result.stdout}")
                return True
        except subprocess.TimeoutExpired:
            print(f"❌ Ошибка: Превышено время ожидания ({timeout}с) для команды Docker.")
            print("   Это обычно означает, что Docker завис или работает слишком медленно.")
            return False
        except Exception as e:
            print(f"❌ Произошла ошибка при выполнении команды: {e}")
            return False
    
    def generate_crypto_materials(self):
        """Генерирует криптографические материалы используя Docker"""
        docker_path = self.get_docker_path(self.base_dir.absolute())
        cmd = [
            "docker", "run", "--rm",
            "--platform", self.platform_arch,
            "-v", f"{docker_path}:/data",
            "-w", "/data",
            "hyperledger/fabric-tools:2.5",
            "cryptogen", "generate",
            "--config=./config/crypto-config.yaml",
            "--output=./organizations"
        ]
        return self.run_docker_command(cmd, "Генерация криптографических материалов")
    
    def generate_genesis_block(self):
        """Генерирует genesis блок"""
        docker_path = self.get_docker_path(self.base_dir.absolute())
        cmd = [
            "docker", "run", "--rm",
            "--platform", self.platform_arch,
            "-v", f"{docker_path}:/data",
            "-w", "/data",
            "-e", "FABRIC_CFG_PATH=/data/config",
            "hyperledger/fabric-tools:2.5",
            "configtxgen",
            "-profile", "TwoOrgsOrdererGenesis",
            "-channelID", "system-channel",
            "-outputBlock", "./channel-artifacts/genesis.block"
        ]
        return self.run_docker_command(cmd, "Генерация genesis блока")
    
    def generate_channel_tx(self, channel_name="npa-channel"):
        """Генерирует транзакцию создания канала"""
        docker_path = self.get_docker_path(self.base_dir.absolute())
        cmd = [
            "docker", "run", "--rm",
            "--platform", self.platform_arch,
            "-v", f"{docker_path}:/data",
            "-w", "/data",
            "-e", "FABRIC_CFG_PATH=/data/config",
            "hyperledger/fabric-tools:2.5",
            "configtxgen",
            "-profile", "TwoOrgsChannel",
            "-channelID", channel_name,
            "-outputCreateChannelTx", f"./channel-artifacts/{channel_name}.tx"
        ]
        return self.run_docker_command(cmd, f"Генерация транзакции создания канала {channel_name}")
    
    def generate_anchor_peers(self, org_name, channel_name="npa-channel"):
        """Генерирует транзакцию обновления anchor peer
        
        Примечание: configtxgen поддерживает только использование профиля для генерации
        anchor peer транзакций. Флаг -channelCreateTxPath не существует.
        """
        docker_path = self.get_docker_path(self.base_dir.absolute())
        
        # Всегда используем профиль (единственный доступный способ)
        # Channel Policies теперь добавлены в профиль, поэтому это должно работать
        cmd = [
            "docker", "run", "--rm",
            "--platform", self.platform_arch,
            "-v", f"{docker_path}:/data",
            "-w", "/data",
            "-e", "FABRIC_CFG_PATH=/data/config",
            "hyperledger/fabric-tools:2.5",
            "configtxgen",
            "-profile", "TwoOrgsChannel",
            "-outputAnchorPeersUpdate", f"./channel-artifacts/{org_name}anchors.tx",
            "-channelID", channel_name,
            "-asOrg", org_name
        ]
        
        return self.run_docker_command(
            cmd,
            f"Генерация транзакции anchor peer для {org_name}"
        )
    
    def cleanup_old_materials(self):
        """Очищает старые криптографические материалы и артефакты"""
        print("\n" + "="*60)
        print("Очистка старых материалов")
        print("="*60)
        
        # Останавливаем сеть, если она запущена, и очищаем volumes
        try:
            print("Проверка запущенных контейнеров...")
            result = subprocess.run(
                ["docker", "compose", "ps", "-q"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                print("⚠️  Найдены запущенные контейнеры. Остановка и очистка volumes...")
                clean_result = subprocess.run(
                    ["docker", "compose", "down", "-v"],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if clean_result.returncode == 0:
                    print("✓ Сеть остановлена и volumes очищены")
                else:
                    print(f"⚠️  Предупреждение: {clean_result.stderr}")
            else:
                # Даже если контейнеры не запущены, убедимся, что volumes очищены
                print("Очистка volumes...")
                subprocess.run(
                    ["docker", "compose", "down", "-v"],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                    timeout=20
                )
                print("✓ Volumes очищены")
        except subprocess.TimeoutExpired:
            print("⚠️  Таймаут при очистке Docker. Пропускаем этот шаг...")
        except Exception as e:
            print(f"⚠️  Не удалось проверить/остановить контейнеры: {e}")
        
        # Удаляем старые директории
        dirs_to_clean = [
            self.orgs_dir,
            self.channel_dir
        ]
        
        for directory in dirs_to_clean:
            if directory.exists():
                try:
                    shutil.rmtree(directory)
                    print(f"✓ Удалено: {directory}")
                except Exception as e:
                    print(f"⚠️  Не удалось удалить {directory}: {e}")
        
        # Создаем пустые директории заново
        self.orgs_dir.mkdir(parents=True, exist_ok=True)
        self.channel_dir.mkdir(parents=True, exist_ok=True)
        print("✓ Директории подготовлены для новой генерации")
    
    def generate_all(self, channel_name="npa-channel", cleanup=True):
        """Генерирует все необходимые артефакты"""
        print("\n" + "="*60)
        print("Генерация криптографических материалов и артефактов канала")
        print("="*60)
        print(f"Канал: {channel_name}")
        print(f"Платформа Docker: {self.platform_arch}")
        print()
        
        # Очистка старых материалов перед генерацией
        if cleanup:
            self.cleanup_old_materials()
        
        # Проверка наличия Docker
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            print(f"✓ Docker найден: {result.stdout.strip()}")
            
            # Дополнительная проверка, что Docker daemon работает
            try:
                subprocess.run(
                    ["docker", "ps"],
                    capture_output=True,
                    check=True,
                    timeout=10
                )
            except subprocess.TimeoutExpired:
                print("❌ Ошибка: Docker daemon не отвечает (таймаут 10с).")
                print("\n📋 Решение:")
                print("   1. Docker Desktop на Windows завис.")
                print("   2. Перезагрузите Docker Desktop (Restart в трее).")
                print("   3. Если не помогает — убейте процессы Docker в Диспетчере задач и запустите снова.")
                return False
            except subprocess.CalledProcessError:
                print("⚠️  Docker установлен, но Docker daemon не запущен.")
                print("\n📋 Решение:")
                print("   1. Запустите Docker Desktop на Windows")
                print("   2. Дождитесь полной загрузки (иконка Docker в системном трее)")
                print("   3. Повторите запуск скрипта")
                return False
                
        except FileNotFoundError:
            print("❌ Docker не установлен или не найден в PATH.")
            print("\n📋 Решение:")
            print("   1. Установите Docker Desktop для Windows:")
            print("      https://www.docker.com/products/docker-desktop")
            print("   2. После установки запустите Docker Desktop")
            print("   3. Повторите запуск скрипта")
            return False
        except subprocess.TimeoutExpired:
            print("❌ Таймаут при проверке Docker. Docker может быть перегружен.")
            print("\n📋 Решение:")
            print("   1. Убедитесь, что Docker Desktop запущен")
            print("   2. Проверьте, что Docker не выполняет другие задачи")
            print("   3. Повторите запуск скрипта")
            return False
        except Exception as e:
            print(f"❌ Ошибка при проверке Docker: {e}")
            print("\n📋 Решение:")
            print("   1. Убедитесь, что Docker Desktop установлен и запущен")
            print("   2. Попробуйте запустить в командной строке: docker --version")
            print("   3. Если Docker не установлен, скачайте его с https://www.docker.com/products/docker-desktop")
            return False
        
        # Проверка наличия конфигурационных файлов
        # Генерируем их заново, чтобы применить все исправления!
        print("\nОбновление конфигурационных файлов (crypto-config.yaml, configtx.yaml, docker-compose.yaml)...")
        generator = FabricConfigGenerator(base_dir=self.base_dir)
        generator.generate_all()
        
        success = True
        
        # Генерация криптографических материалов
        if not self.generate_crypto_materials():
            success = False
        
        # Генерация genesis блока
        if not self.generate_genesis_block():
            success = False
        
        # Генерация транзакции создания канала
        channel_tx_created = False
        if not self.generate_channel_tx(channel_name):
            print("⚠️  Не удалось создать транзакцию канала.")
            success = False
        else:
            # Проверяем, что транзакция канала создана
            channel_tx_path = self.channel_dir / f"{channel_name}.tx"
            if channel_tx_path.exists():
                print(f"✓ Транзакция создания канала найдена: {channel_tx_path}")
                channel_tx_created = True
            else:
                print(f"⚠️  Транзакция создания канала {channel_tx_path} не найдена после генерации")
                success = False
        
        # Генерация anchor peer транзакций (только если транзакция канала создана)
        if channel_tx_created:
            print("\nГенерация anchor peer транзакций...")
            if not self.generate_anchor_peers("Org1MSP", channel_name):
                success = False
            
            if not self.generate_anchor_peers("Org2MSP", channel_name):
                success = False
        else:
            print("\n⚠️  Anchor peer транзакции не будут сгенерированы, так как транзакция канала не создана.")
            print("   Их можно создать позже через channel_setup.py после создания канала.")
        
        if success:
            print("\n" + "="*60)
            print("✓ Все артефакты успешно сгенерированы!")
            print("="*60)
            print("\nТеперь вы можете запустить сеть:")
            print("  docker-compose up -d")
        else:
            print("\n" + "="*60)
            print("❌ Произошли ошибки при генерации")
            print("="*60)
        
        return success


def main():
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Генерация криптографических материалов и артефактов Hyperledger Fabric"
    )
    parser.add_argument(
        "--channel",
        default="npa-channel",
        help="Имя канала (по умолчанию: npa-channel)"
    )
    parser.add_argument(
        "--platform",
        choices=["linux/amd64", "linux/arm64"],
        help="Платформа Docker образа (linux/amd64 или linux/arm64). "
             "Если не указано, определяется автоматически"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Не очищать старые материалы перед генерацией (не рекомендуется)"
    )
    
    args = parser.parse_args()
    
    generator = CryptoMaterialGenerator(platform_arch=args.platform)
    generator.generate_all(args.channel, cleanup=not args.no_cleanup)


if __name__ == "__main__":
    main()

