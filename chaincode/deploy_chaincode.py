#!/usr/bin/env python3
"""
Скрипт для развертывания chaincode в Hyperledger Fabric
Поддерживает external chaincode (Chaincode-as-a-Service - CCAAS)
"""

import subprocess
import sys
import time
import json
import re
import tempfile
import tarfile
from pathlib import Path


class ChaincodeDeployer:
    """Класс для развертывания chaincode в Hyperledger Fabric"""
    
    def __init__(self, base_dir=".."):
        """Инициализация развертывателя chaincode"""
        self.base_dir = Path(base_dir).resolve()
        self.chaincode_dir = Path(__file__).parent
        self.orgs_dir = self.base_dir / "organizations"
        self.channel_dir = self.base_dir / "channel-artifacts"
        
        # Конфигурация chaincode
        self.channel_name = "npa-channel"
        self.chaincode_name = "taskdocument"
        self.chaincode_version = "1.0"
        self.chaincode_sequence = "1" # Incremented to sync peer configurations
        self.chaincode_label = f"{self.chaincode_name}_{self.chaincode_version}"
        self.chaincode_package = self.chaincode_dir / f"{self.chaincode_name}.tar.gz"
        
        # Конфигурация организаций
        self.orgs = {
            "Org1": {
                "msp_id": "Org1MSP",
                "domain": "org1.example.com",
                "peer": "peer0.org1.example.com",
                "peer_port": 7051,
                "admin_user": "Admin@org1.example.com"
            },
            "Org2": {
                "msp_id": "Org2MSP",
                "domain": "org2.example.com",
                "peer": "peer0.org2.example.com",
                "peer_port": 9051,
                "admin_user": "Admin@org2.example.com"
            }
        }
        
        # Orderer конфигурация
        self.orderer = {
            "host": "orderer.example.com",
            "container": "orderer0",
            "port": 7050
        }
        
        # Package ID после установки
        self.package_id = ""  # Используем пустую строку для типа str
    
    def find_orderer_ca_cert(self):
        """Находит CA сертификат orderer"""
        orderer_tls_dir = self.orgs_dir / "ordererOrganizations" / "example.com" / "orderers" / "orderer.example.com" / "tls"
        orderer_msp_dir = self.orgs_dir / "ordererOrganizations" / "example.com" / "orderers" / "orderer.example.com" / "msp" / "tlscacerts"
        
        # Проверяем различные возможные места
        if (orderer_tls_dir / "ca.crt").exists():
            return orderer_tls_dir / "ca.crt"
        
        if orderer_msp_dir.exists():
            pem_files = list(orderer_msp_dir.glob("*.pem"))
            if pem_files:
                return pem_files[0]
        
        if orderer_tls_dir.exists():
            crt_files = list(orderer_tls_dir.glob("*.crt"))
            if crt_files:
                return crt_files[0]
        
        return None
    
    def get_org_config(self, org_name):
        """Получает конфигурацию организации"""
        return self.orgs.get(org_name)
    
    def copy_admin_msp(self, org_name):
        """Копирует Admin MSP в контейнер peer"""
        org_config = self.get_org_config(org_name)
        if not org_config:
            return False
        
        admin_msp = self.orgs_dir / "peerOrganizations" / org_config["domain"] / "users" / org_config["admin_user"] / "msp"
        if not admin_msp.exists():
            print(f"❌ Admin MSP не найден: {admin_msp}")
            return False
        
        peer_container = org_config["peer"]
        admin_msp_container_path = "/etc/hyperledger/fabric/admin-msp"
        
        # Удаляем старую директорию, если она существует (для чистоты)
        remove_cmd = ["docker", "exec", str(peer_container), "rm", "-rf", str(admin_msp_container_path)]
        subprocess.run([str(v) for v in remove_cmd], capture_output=True)
        
        # Копируем MSP Admin в контейнер
        # Используем родительскую директорию для сохранения структуры
        copy_cmd = [
            "docker", "cp",
            str(admin_msp.absolute()) + "/.",
            f"{peer_container}:{admin_msp_container_path}"
        ]
        result = subprocess.run([str(v) for v in copy_cmd], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Ошибка копирования MSP: {result.stderr}")
            return False
            
        # Для работы NodeOUs нужно, чтобы в MSP была директория config.yaml
        # Копируем config.yaml из основного MSP организации, если его нет у пользователя
        if not (admin_msp / "config.yaml").exists():
            org_msp_config = self.orgs_dir / "peerOrganizations" / org_config["domain"] / "msp" / "config.yaml"
            if org_msp_config.exists():
                copy_config_cmd = [
                    "docker", "cp",
                    str(org_msp_config.absolute()),
                    f"{peer_container}:{admin_msp_container_path}/config.yaml"
                ]
                subprocess.run([str(v) for v in copy_config_cmd], capture_output=True)
                
        return True
    
    def copy_orderer_ca(self, org_name):
        """Копирует orderer CA сертификат в контейнер peer"""
        orderer_ca = self.find_orderer_ca_cert()
        if not orderer_ca:
            return False
        
        org_config = self.get_org_config(org_name)
        if not org_config:
            return False
        
        peer_container = org_config["peer"]
        paths = [
            f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem",
            f"{peer_container}:/etc/hyperledger/fabric/orderer-ca.pem"
        ]
        
        for path in paths:
            copy_cmd = [
                "docker", "cp",
                str(orderer_ca.absolute()),
                path
            ]
            subprocess.run(copy_cmd, capture_output=True)
        
        return True
    
    def run_peer_command(self, org_name, command, description):
        """Выполняет команду peer через Docker"""
        org_config = self.get_org_config(org_name)
        if not org_config:
            print(f"❌ Неизвестная организация: {org_name}")
            return False, ""
        
        peer_container = org_config["peer"]
        
        # Копируем Admin MSP
        self.copy_admin_msp(org_name)
        
        # Формируем команду
        cmd = [
            "docker", "exec",
            "-e", f"CORE_PEER_LOCALMSPID={org_config['msp_id']}",
            "-e", "CORE_PEER_TLS_ENABLED=true",
            "-e", f"CORE_PEER_ADDRESS={org_config['peer']}:{org_config['peer_port']}",
            "-e", "CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt",
            "-e", "CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/admin-msp",
            "-e", "FABRIC_LOGGING_SPEC=DEBUG", # Временная диагностика
            "-w", "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            peer_container,
            "peer"
        ] + command
        
        print(f"\n{'='*60}")
        print(f"{description} ({org_name})")
        print(f"{'='*60}")
        print(f"Выполняется: {' '.join([str(i) for i in cmd])}")
        
        result = subprocess.run([str(i) for i in cmd], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Ошибка: {result.stderr}")
            if result.stdout:
                print(f"Вывод: {result.stdout}")
            return False, result.stderr or ""
        
        print(f"✓ Успешно")
        if result.stdout:
            print(result.stdout)
        
        return True, result.stdout
    
    def package_chaincode(self):
        """Создает package для external chaincode (CCAAS)"""
        print("\n" + "="*60)
        print("Упаковка chaincode (CCAAS)")
        print("="*60)
        
        # Структура package для CCAAS:
        # package.tar.gz
        #   ├── metadata.json (type: "ccaas")
        #   └── code.tar.gz
        #       └── connection.json
        
        self.chaincode_package.parent.mkdir(parents=True, exist_ok=True)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Создаем metadata.json
            metadata = {
                "type": "ccaas",
                "label": self.chaincode_label
            }
            metadata_path = temp_path / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print("✓ metadata.json создан")
            
            # Создаем connection.json
            connection = {
                "address": "chaincode-server:9999",
                "dial_timeout": "10s",
                "tls_required": False,
                "client_auth_required": False
            }
            connection_path = temp_path / "connection.json"
            with open(connection_path, 'w') as f:
                json.dump(connection, f, indent=2)
            print("✓ connection.json создан")
            
            # Создаем code.tar.gz
            code_tar_path = temp_path / "code.tar.gz"
            with tarfile.open(code_tar_path, "w:gz") as code_tar:
                code_tar.add(connection_path, arcname="connection.json")
            print("✓ code.tar.gz создан")
            
            # Создаем финальный package.tar.gz
            with tarfile.open(self.chaincode_package, "w:gz") as package_tar:
                package_tar.add(metadata_path, arcname="metadata.json")
                package_tar.add(code_tar_path, arcname="code.tar.gz")
            
            print(f"✓ Package создан: {self.chaincode_package}")
        
        return True
    
    def install_chaincode(self):
        """Устанавливает chaincode на peer'ы и получает package-id"""
        print("\n" + "="*60)
        print("Установка chaincode на peer'ы")
        print("="*60)
        
        if not self.chaincode_package.exists():
            print(f"❌ Package не найден: {self.chaincode_package}")
            return False
        
        package_name = self.chaincode_package.name
        package_ids = {}
        
        # Устанавливаем на каждый peer
        for org_name in self.orgs.keys():
            org_config = self.get_org_config(org_name)
            peer_container = org_config["peer"]
            
            # Копируем package в контейнер
            copy_cmd = [
                "docker", "cp",
                str(self.chaincode_package.absolute()),
                f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/{package_name}"
            ]
            subprocess.run(copy_cmd, capture_output=True)
            
            # Устанавливаем chaincode
            result, output = self.run_peer_command(
                org_name,
                ["lifecycle", "chaincode", "install", f"./{package_name}"],
                f"Установка chaincode на {org_name}"
            )
            
            if result:
                # Получаем package-id
                query_result, query_output = self.run_peer_command(
                    org_name,
                    ["lifecycle", "chaincode", "queryinstalled"],
                    f"Получение package-id для {org_name}"
                )
                
                if query_result and query_output:
                    # Парсим package-id
                    package_id = self._parse_package_id(query_output)
                    if package_id:
                        package_ids[org_name] = package_id
                        print(f"✓ Package ID для {org_name}: {package_id}")
        
        # Находим общий package-id, который есть у обеих организаций
        if len(package_ids) == 2:
            org1_id = str(package_ids["Org1"])
            org2_id = str(package_ids["Org2"])
            
            # Если package-id одинаковые
            if org1_id == org2_id:
                self.package_id = org1_id
                print(f"\n✓ Используется общий package-id: {self.package_id}")
            else:
                # Получаем все package-id с обоих peer'ов
                print(f"\n⚠️  Разные package-id после установки:")
                print(f"   Org1: {org1_id}")
                print(f"   Org2: {org2_id}")
                
                # Запрашиваем все установленные package-id с обоих peer'ов
                all_package_ids = {}
                for org_name in ["Org1", "Org2"]:
                    query_result, query_output = self.run_peer_command(
                        org_name,
                        ["lifecycle", "chaincode", "queryinstalled"],
                        f"Получение всех package-id для {org_name}"
                    )
                    if query_result and query_output:
                        # Извлекаем все package-id для этого chaincode
                        org_package_ids = []
                        for line in query_output.split('\n'):
                            if self.chaincode_label in line and 'Package ID:' in line:
                                match = re.search(r'Package ID:\s*([^\s,]+)', line)
                                if match:
                                    org_package_ids.append(match.group(1).strip())
                        all_package_ids[org_name] = org_package_ids
                
                # Находим общий package-id
                org1_ids = set(all_package_ids.get("Org1", []))
                org2_ids = set(all_package_ids.get("Org2", []))
                common_ids = org1_ids.intersection(org2_ids)
                
                if common_ids:
                    # Используем первый общий package-id
                    self.package_id = list(common_ids)[0]
                    print(f"✓ Найден общий package-id: {self.package_id}")
                else:
                    # Если общего нет, используем последний от Org1
                    self.package_id = str(org1_id)
                    print(f"⚠️  Общего package-id не найдено, используем от Org1: {self.package_id}")
        elif len(package_ids) == 1:
            self.package_id = str(list(package_ids.values())[0])
            print(f"\n✓ Используется package-id: {self.package_id} (только одна организация)")
        else:
            print("❌ Не удалось получить package-id ни от одной организации")
            return False
        
        return True
    
    def _parse_package_id(self, output):
        """Парсит package-id из вывода queryinstalled (берет последний)"""
        package_ids: list = []
        for line in output.split('\n'):
            if self.chaincode_label in line and 'Package ID:' in line:
                # Ищем "Package ID:" или просто ID после метки
                match = re.search(r'Package ID:\s*([^\s,]+)', line)
                if match:
                    package_ids.append(match.group(1).strip())
                else:
                    # Альтернативный формат
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'Package ID:' in part and i + 1 < len(parts):
                            package_ids.append(parts[i + 1].strip().rstrip(','))
        
        # Возвращаем последний package-id (самый свежий)
        return package_ids[-1] if package_ids else ""
    
    def approve_chaincode(self):
        """Одобряет chaincode от каждой организации"""
        print("\n" + "="*60)
        print("Одобрение chaincode организациями")
        print("="*60)
        
        if not self.package_id:
            print("❌ Package ID не найден")
            return False
        
        orderer_ca = self.find_orderer_ca_cert()
        if not orderer_ca:
            print("❌ Не найден CA сертификат orderer")
            return False
        
        success = True
        
        for org_name in self.orgs.keys():
            # Копируем orderer CA
            self.copy_orderer_ca(org_name)
            
            org_config = self.get_org_config(org_name)
            
            # Одобряем chaincode
            result, output = self.run_peer_command(
                org_name,
                [
                    "lifecycle", "chaincode", "approveformyorg",
                    "--orderer", f"{self.orderer['container']}:{self.orderer['port']}",
                    "--ordererTLSHostnameOverride", self.orderer["host"],
                    "--channelID", self.channel_name,
                    "--name", self.chaincode_name,
                    "--version", self.chaincode_version,
                    "--package-id", self.package_id,
                    "--sequence", self.chaincode_sequence,
                    "--tls",
                    "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem",
                    "--peerAddresses", f"{org_config['peer']}:{org_config['peer_port']}",
                    "--tlsRootCertFiles", "/etc/hyperledger/fabric/tls/ca.crt"
                ],
                f"Одобрение chaincode от {org_name}"
            )
            
            # Обрабатываем таймауты - транзакция может быть отправлена, но блок не получен
            if not result:
                # Проверяем, был ли это таймаут (транзакция отправлена, но блок не получен)
                timeout_keywords = ["timed out", "deadline exceeded", "context finished", "waiting for txid"]
                is_timeout = any(keyword in output.lower() for keyword in timeout_keywords)
                
                if is_timeout:
                    print(f"⚠️  Таймаут получения блока для {org_name}, но транзакция могла быть отправлена")
                    print(f"   Проверим готовность к коммиту позже...")
                    # Не считаем это критической ошибкой - проверим готовность позже
                else:
                    print(f"❌ Ошибка одобрения для {org_name}: {output}")
                    success = False
        
        # Пауза для обработки транзакций (даже если были таймауты)
        print("\n⏳ Ожидание обработки одобрений orderer...")
        time.sleep(10)
        
        # Проверяем локальные одобрения на каждом peer
        print("\n🔍 Проверка локальных одобрений на peer'ах...")
        local_approvals = {}
        for org_name in self.orgs.keys():
            result, output = self.run_peer_command(
                org_name,
                [
                    "lifecycle", "chaincode", "queryapproved",
                    "-C", self.channel_name,
                    "-n", self.chaincode_name,
                    "--sequence", self.chaincode_sequence
                ],
                f"Проверка локального одобрения для {org_name}"
            )
            if result and output:
                if (self.package_id and self.package_id in output) or self.chaincode_name in output:
                    local_approvals[org_name] = True
                    print(f"✓ {org_name}: локальное одобрение найдено")
                else:
                    local_approvals[org_name] = False
                    print(f"⚠️  {org_name}: локальное одобрение не найдено в выводе")
            else:
                # Ошибка при запросе - значит одобрения точно нет
                local_approvals[org_name] = False
                print(f"⚠️  {org_name}: локальное одобрение не создано (транзакция не была обработана)")
        
        # Анализируем результаты
        all_approved_locally = all(local_approvals.values()) if local_approvals else False
        
        # Проверяем готовность к коммиту - это покажет, были ли одобрения зафиксированы на канале
        print("\n🔍 Проверка статуса одобрений на канале...")
        readiness = self.check_commit_readiness()
        
        if readiness:
            print("✓ Одобрения успешно зафиксированы на канале, готовы к коммиту")
            return True
        
        # Если локальные одобрения не созданы - критическая ошибка
        if not all_approved_locally:
            print("\n" + "="*60)
            print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Одобрения не созданы")
            print("="*60)
            print("Локальные одобрения не были созданы на peer'ах.")
            print("Это означает, что транзакции одобрения не были обработаны.")
            print("\nПричина:")
            print("- Peer'ы не могут получать блоки от orderer для подтверждения транзакций")
            print("- Транзакции одобрения не доходят до orderer")
            print("- Канал был создан из старой транзакции без orderer endpoints")
            print("\nРешение:")
            print("Канал необходимо пересоздать с правильной конфигурацией.")
            print("\n📋 ПОШАГОВАЯ ИНСТРУКЦИЯ:")
            print("="*60)
            print("1. Остановите сеть и очистите volumes:")
            print("   python network_setup.py clean")
            print()
            print("2. Убедитесь, что configtx.yaml содержит секцию Orderer в профиле TwoOrgsChannel")
            print("   (Она должна быть там, если вы использовали generate_fabric_config.py)")
            print()
            print("3. Перегенерируйте криптографические материалы и артефакты:")
            print("   python generate_crypto_materials.py")
            print("   (Скрипт автоматически очистит старые материалы и volumes)")
            print()
            print("4. Запустите сеть:")
            print("   python network_setup.py start")
            print()
            print("5. Пересоздайте канал:")
            print("   python channel_setup.py")
            print()
            print("6. Повторите развертывание chaincode:")
            print("   python deploy_chaincode.py")
            print("="*60)
            print("\n⚠️  Без зафиксированных одобрений коммит chaincode невозможен.")
            print("="*60)
            return False
        
        # Локальные одобрения есть, но не зафиксированы на канале
        print("\n" + "="*60)
        print("⚠️  ПРОБЛЕМА: Одобрения не зафиксированы на канале")
        print("="*60)
        print("Локальные одобрения созданы, но не записаны в конфигурацию канала.")
        print("\nВозможные причины:")
        print("1. Peer'ы не могут получать блоки от orderer (Deliver API)")
        print("2. Транзакции одобрения не были включены в блоки orderer")
        print("3. Конфигурация канала не синхронизирована")
        print("\nРешение:")
        print("1. Проверьте логи orderer: docker logs orderer0 | grep lifecycle")
        print("2. Проверьте логи peer'ов: docker logs peer0.org1.example.com | grep -i orderer")
        print("3. Обновите конфигурацию канала, добавив orderer endpoints")
        print("4. Попробуйте повторить одобрение после исправления конфигурации")
        print("\nПродолжаем попытку коммита (вероятно, не сработает)...")
        print("="*60)
        # Продолжаем - возможно коммит все равно сработает
        return True
    
    def check_commit_readiness(self):
        """Проверяет готовность chaincode к коммиту"""
        print("\n" + "="*60)
        print("Проверка готовности к коммиту")
        print("="*60)
        
        # Копируем необходимые сертификаты
        self.copy_orderer_ca("Org1")
        
        org_config = self.get_org_config("Org1")
        peer_container = org_config["peer"]
        
        # Копируем TLS CA сертификаты
        for org_name in self.orgs.keys():
            org_cfg = self.get_org_config(org_name)
            tls_ca = self.orgs_dir / "peerOrganizations" / org_cfg["domain"] / "peers" / org_cfg["peer"] / "tls" / "ca.crt"
            if tls_ca.exists():
                copy_cmd = [
                    "docker", "cp",
                    str(tls_ca.absolute()),
                    f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/{org_cfg['domain'].split('.')[0]}-tls-ca.crt"
                ]
                subprocess.run(copy_cmd, capture_output=True)
        
        # Проверяем готовность
        result, output = self.run_peer_command(
            "Org1",
            [
                "lifecycle", "chaincode", "checkcommitreadiness",
                "--channelID", self.channel_name,
                "--name", self.chaincode_name,
                "--version", self.chaincode_version,
                "--sequence", self.chaincode_sequence,
                "--peerAddresses", f"{org_config['peer']}:{org_config['peer_port']}",
                "--tlsRootCertFiles", "/opt/gopath/src/github.com/hyperledger/fabric/peer/org1-tls-ca.crt"
            ],
            "Проверка готовности к коммиту"
        )
        
        if result and output:
            print(f"Статус готовности:\n{output}")
            if "Org1MSP: true" in output and "Org2MSP: true" in output:
                print("✓ Chaincode готов к коммиту")
                return True
        
        return False
    
    def commit_chaincode(self):
        """Коммитит chaincode в канал"""
        print("\n" + "="*60)
        print("Коммит chaincode в канал")
        print("="*60)
        
        orderer_ca = self.find_orderer_ca_cert()
        if not orderer_ca:
            print("❌ Не найден CA сертификат orderer")
            return False
        
        # Подготавливаем сертификаты для Org1 (от его имени выполняется commit)
        self.copy_orderer_ca("Org1")
        
        org1_config = self.get_org_config("Org1")
        org2_config = self.get_org_config("Org2")
        peer_container = org1_config["peer"]
        
        # Копируем TLS CA сертификаты обоих организаций
        for org_name, org_config in self.orgs.items():
            tls_ca = self.orgs_dir / "peerOrganizations" / org_config["domain"] / "peers" / org_config["peer"] / "tls" / "ca.crt"
            if tls_ca.exists():
                org_short = org_config["domain"].split('.')[0]
                copy_cmd = [
                    "docker", "cp",
                    str(tls_ca.absolute()),
                    f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/{org_short}-tls-ca.crt"
                ]
                subprocess.run(copy_cmd, capture_output=True)
        
        # Выполняем коммит
        result, output = self.run_peer_command(
            "Org1",
            [
                "lifecycle", "chaincode", "commit",
                "--orderer", f"{self.orderer['container']}:{self.orderer['port']}",
                "--ordererTLSHostnameOverride", self.orderer["host"],
                "--channelID", self.channel_name,
                "--name", self.chaincode_name,
                "--version", self.chaincode_version,
                "--sequence", self.chaincode_sequence,
                "--tls",
                "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem",
                "--peerAddresses", f"{org1_config['peer']}:{org1_config['peer_port']}",
                "--peerAddresses", f"{org2_config['peer']}:{org2_config['peer_port']}",
                "--tlsRootCertFiles", "/opt/gopath/src/github.com/hyperledger/fabric/peer/org1-tls-ca.crt",
                "--tlsRootCertFiles", "/opt/gopath/src/github.com/hyperledger/fabric/peer/org2-tls-ca.crt"
            ],
            "Коммит chaincode в канал"
        )
        
        # Обрабатываем ошибки коммита
        if not result:
            timeout_keywords = ["timed out", "deadline exceeded", "context finished", "waiting for txid"]
            is_timeout = any(keyword in output.lower() for keyword in timeout_keywords)
            
            if is_timeout:
                print("⚠️  Таймаут получения блока при коммите, но транзакция могла быть отправлена")
            elif "not agreed to" in output.lower() or "not approved" in output.lower():
                print("\n" + "="*60)
                print("❌ КРИТИЧЕСКАЯ ОШИБКА: Коммит невозможен")
                print("="*60)
                print("Одобрения не зафиксированы на канале.")
                print("Это означает, что транзакции одобрения не были обработаны orderer.")
                print("\nПричина:")
                print("- Peer'ы не могут получать блоки от orderer")
                print("- Канал был создан из старой транзакции без orderer endpoints")
                print("\nРешение:")
                print("Необходимо пересоздать канал с правильной конфигурацией.")
                print("См. инструкции выше в разделе 'КРИТИЧЕСКАЯ ПРОБЛЕМА: Одобрения не созданы'")
                print("="*60)
                return False
        
        # Проверяем статус коммита
        print("\n🔍 Проверка статуса коммита...")
        query_result, query_output = self.run_peer_command(
            "Org1",
            [
                "lifecycle", "chaincode", "querycommitted",
                "-C", self.channel_name,
                "-n", self.chaincode_name
            ],
            "Проверка закоммиченного chaincode"
        )
        
        if query_result and query_output:
            if self.chaincode_name in query_output and self.chaincode_version in query_output:
                print("✓ Chaincode успешно закоммичен!")
                return True
        
        return result
    
    def deploy(self):
        """Выполняет полное развертывание chaincode"""
        print("\n" + "="*60)
        print("Развертывание chaincode")
        print("="*60)
        print(f"Chaincode: {self.chaincode_name}")
        print(f"Версия: {self.chaincode_version}")
        print(f"Канал: {self.channel_name}")
        print(f"Sequence: {self.chaincode_sequence}")
        print("="*60)
        
        # Шаг 1: Упаковка
        if not self.package_chaincode():
            print("\n❌ Ошибка на этапе упаковки")
            return False
        
        # Шаг 2: Установка
        if not self.install_chaincode():
            print("\n❌ Ошибка на этапе установки")
            return False
        
        # Шаг 3: Одобрение
        if not self.approve_chaincode():
            print("\n❌ Ошибка на этапе одобрения")
            return False
        
        # Шаг 4: Проверка готовности (опционально)
        self.check_commit_readiness()
        
        # Шаг 5: Коммит
        if not self.commit_chaincode():
            print("\n❌ Ошибка на этапе коммита")
            return False
        
        print("\n" + "="*60)
        print("✓ Chaincode успешно развернут!")
        print("="*60)
        
        return True


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Развертывание chaincode в Hyperledger Fabric")
    parser.add_argument("--channel", default="npa-channel", help="Имя канала")
    parser.add_argument("--name", default="taskdocument", help="Имя chaincode")
    parser.add_argument("--version", default="1.0", help="Версия chaincode")
    parser.add_argument("--sequence", default="1", help="Sequence номер")
    
    args = parser.parse_args()
    
    deployer = ChaincodeDeployer()
    deployer.channel_name = args.channel
    deployer.chaincode_name = args.name
    deployer.chaincode_version = args.version
    deployer.chaincode_sequence = args.sequence
    deployer.chaincode_label = f"{deployer.chaincode_name}_{deployer.chaincode_version}"
    deployer.chaincode_package = deployer.chaincode_dir / f"{deployer.chaincode_name}.tar.gz"
    
    success = deployer.deploy()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
