#!/usr/bin/env python3
"""
Генератор конфигурации Hyperledger Fabric v2.x
Создает минимальную конфигурацию с двумя организациями и одним каналом
"""

import os
import sys
try:
    import yaml # type: ignore
except ImportError:
    print("❌ Ошибка: пакет 'PyYAML' не установлен.")
    print("   Установите его командой: pip install PyYAML")
    sys.exit(1)
from pathlib import Path


class FabricConfigGenerator:
    def __init__(self, base_dir="."):
        self.base_dir = Path(base_dir)
        self.config_dir = self.base_dir / "config"
        self.orgs_dir = self.base_dir / "organizations"
        self.channel_dir = self.base_dir / "channel-artifacts"
        
    def create_directories(self):
        """Создает необходимую структуру директорий"""
        directories = [
            self.config_dir,
            self.orgs_dir / "ordererOrganizations" / "example.com",
            self.orgs_dir / "peerOrganizations" / "org1.example.com",
            self.orgs_dir / "peerOrganizations" / "org2.example.com",
            self.channel_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✓ Создана директория: {directory}")
    
    def generate_crypto_config(self):
        """Генерирует crypto-config.yaml"""
        crypto_config = {
            'OrdererOrgs': [
                {
                    'Name': 'Orderer',
                    'Domain': 'example.com',
                    'Specs': [
                        {'Hostname': 'orderer'}
                    ]
                }
            ],
            'PeerOrgs': [
                {
                    'Name': 'Org1',
                    'Domain': 'org1.example.com',
                    'EnableNodeOUs': True,
                    'Template': {
                        'Count': 1
                    },
                    'Users': {
                        'Count': 1
                    }
                },
                {
                    'Name': 'Org2',
                    'Domain': 'org2.example.com',
                    'EnableNodeOUs': True,
                    'Template': {
                        'Count': 1
                    },
                    'Users': {
                        'Count': 1
                    }
                }
            ]
        }
        
        config_path = self.config_dir / "crypto-config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(crypto_config, f, default_flow_style=False, allow_unicode=True)
        print(f"✓ Создан файл: {config_path}")
        return config_path
    
    def generate_configtx(self):
        """Генерирует configtx.yaml"""
        configtx = {
            'Organizations': [
                {
                    'Name': 'OrdererOrg',
                    'ID': 'OrdererMSP',
                    'MSPDir': '../organizations/ordererOrganizations/example.com/msp',
                    'OrdererEndpoints': [
                        'orderer.example.com:7050'
                    ],
                    'Policies': {
                        'Readers': {
                            'Type': 'Signature',
                            'Rule': "OR('OrdererMSP.member')"
                        },
                        'Writers': {
                            'Type': 'Signature',
                            'Rule': "OR('OrdererMSP.member')"
                        },
                        'Admins': {
                            'Type': 'Signature',
                            'Rule': "OR('OrdererMSP.admin')"
                        }
                    }
                },
                {
                    'Name': 'Org1MSP',
                    'ID': 'Org1MSP',
                    'MSPDir': '../organizations/peerOrganizations/org1.example.com/msp',
                    'Policies': {
                        'Readers': {
                            'Type': 'Signature',
                            'Rule': "OR('Org1MSP.admin', 'Org1MSP.peer', 'Org1MSP.client')"
                        },
                        'Writers': {
                            'Type': 'Signature',
                            'Rule': "OR('Org1MSP.admin', 'Org1MSP.client')"
                        },
                        'Admins': {
                            'Type': 'Signature',
                            'Rule': "OR('Org1MSP.admin')"
                        },
                        'Endorsement': {
                            'Type': 'Signature',
                            'Rule': "OR('Org1MSP.peer')"
                        }
                    },
                    'AnchorPeers': [
                        {
                            'Host': 'peer0.org1.example.com',
                            'Port': 7051
                        }
                    ]
                },
                {
                    'Name': 'Org2MSP',
                    'ID': 'Org2MSP',
                    'MSPDir': '../organizations/peerOrganizations/org2.example.com/msp',
                    'Policies': {
                        'Readers': {
                            'Type': 'Signature',
                            'Rule': "OR('Org2MSP.admin', 'Org2MSP.peer', 'Org2MSP.client')"
                        },
                        'Writers': {
                            'Type': 'Signature',
                            'Rule': "OR('Org2MSP.admin', 'Org2MSP.client')"
                        },
                        'Admins': {
                            'Type': 'Signature',
                            'Rule': "OR('Org2MSP.admin')"
                        },
                        'Endorsement': {
                            'Type': 'Signature',
                            'Rule': "OR('Org2MSP.peer')"
                        }
                    },
                    'AnchorPeers': [
                        {
                            'Host': 'peer0.org2.example.com',
                            'Port': 9051
                        }
                    ]
                }
            ],
            'Capabilities': {
                'Channel': {
                    'V2_0': True
                },
                'Orderer': {
                    'V2_0': True
                },
                'Application': {
                    'V2_0': True
                }
            },
            'Application': {
                'Organizations': None,
                'Policies': {
                    'Readers': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Readers'
                    },
                    'Writers': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Writers'
                    },
                    'Admins': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'MAJORITY Admins'
                    },
                    'LifecycleEndorsement': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'MAJORITY Endorsement'
                    },
                    'Endorsement': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'MAJORITY Endorsement'
                    }
                },
                'Capabilities': {
                    'V2_0': True
                }
            },
            'Orderer': {
                'OrdererType': 'etcdraft',
                'EtcdRaft': {
                    'Consenters': [
                        {
                            'Host': 'orderer.example.com',
                            'Port': 7050,
                            'ClientTLSCert': '../organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt',
                            'ServerTLSCert': '../organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt'
                        }
                    ]
                },
                'Organizations': None,
                'Policies': {
                    'Readers': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Readers'
                    },
                    'Writers': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Writers'
                    },
                    'Admins': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'MAJORITY Admins'
                    },
                    'BlockValidation': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Writers'
                    }
                },
                'Capabilities': {
                    'V2_0': True
                },
                'BatchTimeout': '2s',
                'BatchSize': {
                    'MaxMessageCount': 10,
                    'AbsoluteMaxBytes': '99 MB',
                    'PreferredMaxBytes': '512 KB'
                }
            },
            'Channel': {
                'Policies': {
                    'Readers': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Readers'
                    },
                    'Writers': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'ANY Writers'
                    },
                    'Admins': {
                        'Type': 'ImplicitMeta',
                        'Rule': 'MAJORITY Admins'
                    }
                },
                'Capabilities': {
                    'V2_0': True
                }
            },
            'Profiles': {
                'TwoOrgsOrdererGenesis': {
                    'Orderer': {
                        'OrdererType': 'etcdraft',
                        # Адреса orderer для OrdererEndpoints
                        'Addresses': [
                            'orderer.example.com:7050'
                        ],
                        'EtcdRaft': {
                            'Consenters': [
                                {
                                    'Host': 'orderer.example.com',
                                    'Port': 7050,
                                    'ClientTLSCert': '../organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt',
                                    'ServerTLSCert': '../organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt'
                                }
                            ]
                        },
                        'Organizations': ['OrdererOrg'],
                        'Policies': {
                            'Readers': {
                                'Type': 'ImplicitMeta',
                                'Rule': 'ANY Readers'
                            },
                            'Writers': {
                                'Type': 'ImplicitMeta',
                                'Rule': 'ANY Writers'
                            },
                            'Admins': {
                                'Type': 'ImplicitMeta',
                                'Rule': 'MAJORITY Admins'
                            },
                            'BlockValidation': {
                                'Type': 'ImplicitMeta',
                                'Rule': 'ANY Writers'
                            }
                        },
                        'Capabilities': {
                            'V2_0': True
                        },
                        'BatchTimeout': '2s',
                        'BatchSize': {
                            'MaxMessageCount': 10,
                            'AbsoluteMaxBytes': '99 MB',
                            'PreferredMaxBytes': '512 KB'
                        }
                    },
                    'Consortiums': {
                        'SampleConsortium': {
                            'Organizations': ['Org1MSP', 'Org2MSP']
                        }
                    }
                },
                'TwoOrgsChannel': {
                    'Consortium': 'SampleConsortium',
                    'Application': {
                        'Organizations': ['Org1MSP', 'Org2MSP'],
                        'Policies': {
                            'Readers': {
                                'Type': 'ImplicitMeta',
                                'Rule': 'ANY Readers'
                            },
                            'Writers': {
                                'Type': 'ImplicitMeta',
                                'Rule': 'ANY Writers'
                            },
                            'Admins': {
                                'Type': 'ImplicitMeta',
                                'Rule': 'MAJORITY Admins'
                            },
                            'LifecycleEndorsement': {
                                'Type': 'ImplicitMeta',
                                'Rule': 'MAJORITY Endorsement'
                            },
                            'Endorsement': {
                                'Type': 'ImplicitMeta',
                                'Rule': 'MAJORITY Endorsement'
                            }
                        },
                        'Capabilities': {
                            'V2_0': True
                        }
                    },
                    'Orderer': {
                        'OrdererType': 'etcdraft',
                        'EtcdRaft': {
                            'Consenters': [
                                {
                                    'Host': 'orderer.example.com',
                                    'Port': 7050,
                                    'ClientTLSCert': '../organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt',
                                    'ServerTLSCert': '../organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/server.crt'
                                }
                            ]
                        },
                        'Organizations': ['OrdererOrg'],
                        'Policies': {
                            'Readers': {
                                'Type': 'ImplicitMeta',
                                'Rule': 'ANY Readers'
                            },
                            'Writers': {
                                'Type': 'ImplicitMeta',
                                'Rule': 'ANY Writers'
                            },
                            'Admins': {
                                'Type': 'ImplicitMeta',
                                'Rule': 'MAJORITY Admins'
                            },
                            'BlockValidation': {
                                'Type': 'ImplicitMeta',
                                'Rule': 'ANY Writers'
                            }
                        },
                        'Capabilities': {
                            'V2_0': True
                        },
                        'BatchTimeout': '2s',
                        'BatchSize': {
                            'MaxMessageCount': 10,
                            'AbsoluteMaxBytes': '99 MB',
                            'PreferredMaxBytes': '512 KB'
                        }
                    }
                }
            }
        }
        
        config_path = self.config_dir / "configtx.yaml"
        
        # PyYAML не поддерживает anchors/aliases напрямую через dump,
        # поэтому генерируем YAML вручную для правильного использования anchors
        self._write_configtx_with_anchors(config_path, configtx)
        
        print(f"✓ Создан файл: {config_path}")
        return config_path
    
    def _write_configtx_with_anchors(self, config_path, configtx):
        """Записывает configtx.yaml с правильными YAML anchors и aliases"""
        lines: list[str] = []
        
        # Organizations с anchors
        lines.append("Organizations:")
        org_anchors = {}
        
        for i, org in enumerate(configtx['Organizations']):
            # Anchor имя должно совпадать с Name организации
            anchor_name = org['Name']
            org_anchors[org['Name']] = anchor_name
            
            lines.append(f"- &{anchor_name}")
            lines.append(f"  Name: {org['Name']}")
            lines.append(f"  ID: {org['ID']}")
            lines.append(f"  MSPDir: {org['MSPDir']}")
            lines.append("  Policies:")
            for policy_name, policy in org['Policies'].items():
                lines.append(f"    {policy_name}:")
                lines.append(f"      Type: {policy['Type']}")
                lines.append(f"      Rule: {policy['Rule']}")
            
            if 'AnchorPeers' in org:
                lines.append("  AnchorPeers:")
                for anchor_peer in org['AnchorPeers']:
                    lines.append(f"  - Host: {anchor_peer['Host']}")
                    lines.append(f"    Port: {anchor_peer['Port']}")
            
            if 'OrdererEndpoints' in org:
                lines.append("  OrdererEndpoints:")
                for addr in org['OrdererEndpoints']:
                    lines.append(f"  - {addr}")
        
        lines.append("")
        
        # Capabilities
        lines.append("Capabilities:")
        for cap_type, cap_value in configtx['Capabilities'].items():
            lines.append(f"  {cap_type}:")
            # cap_value может быть словарем {'V2_0': True} или просто True
            if isinstance(cap_value, dict):
                for version, enabled in cap_value.items():
                    lines.append(f"    {version}: {str(enabled).lower()}")
            else:
                lines.append(f"    V2_0: {str(cap_value).lower()}")
        lines.append("")
        
        # Application
        lines.append("Application:")
        lines.append("  Organizations: null")
        lines.append("  Policies:")
        for policy_name, policy in configtx['Application']['Policies'].items():
            lines.append(f"    {policy_name}:")
            lines.append(f"      Type: {policy['Type']}")
            lines.append(f"      Rule: {policy['Rule']}")
        lines.append("  Capabilities:")
        lines.append(f"    V2_0: {str(configtx['Application']['Capabilities']['V2_0']).lower()}")
        lines.append("")
        
        # Orderer
        lines.append("Orderer:")
        lines.append(f"  OrdererType: {configtx['Orderer']['OrdererType']}")
        lines.append("  EtcdRaft:")
        lines.append("    Consenters:")
        for consenter in configtx['Orderer']['EtcdRaft']['Consenters']:
            lines.append(f"    - Host: {consenter['Host']}")
            lines.append(f"      Port: {consenter['Port']}")
            lines.append(f"      ClientTLSCert: {consenter['ClientTLSCert']}")
            lines.append(f"      ServerTLSCert: {consenter['ServerTLSCert']}")
        lines.append("  Organizations: null")
        lines.append("  Policies:")
        for policy_name, policy in configtx['Orderer']['Policies'].items():
            lines.append(f"    {policy_name}:")
            lines.append(f"      Type: {policy['Type']}")
            lines.append(f"      Rule: {policy['Rule']}")
        lines.append("  Capabilities:")
        lines.append(f"    V2_0: {str(configtx['Orderer']['Capabilities']['V2_0']).lower()}")
        lines.append(f"  BatchTimeout: {configtx['Orderer']['BatchTimeout']}")
        lines.append("  BatchSize:")
        batch_size = configtx['Orderer']['BatchSize']
        lines.append(f"    MaxMessageCount: {batch_size['MaxMessageCount']}")
        lines.append(f"    AbsoluteMaxBytes: {batch_size['AbsoluteMaxBytes']}")
        lines.append(f"    PreferredMaxBytes: {batch_size['PreferredMaxBytes']}")
        lines.append("")
        
        # Channel
        lines.append("Channel:")
        lines.append("  Policies:")
        for policy_name, policy in configtx['Channel']['Policies'].items():
            lines.append(f"    {policy_name}:")
            lines.append(f"      Type: {policy['Type']}")
            lines.append(f"      Rule: {policy['Rule']}")
        lines.append("  Capabilities:")
        lines.append(f"    V2_0: {str(configtx['Channel']['Capabilities']['V2_0']).lower()}")
        lines.append("")
        
        # Profiles с aliases
        lines.append("Profiles:")
        lines.append("  TwoOrgsOrdererGenesis:")
        lines.append("    Orderer:")
        lines.append("      OrdererType: etcdraft")
        lines.append("      EtcdRaft:")
        lines.append("        Consenters:")
        for consenter in configtx['Orderer']['EtcdRaft']['Consenters']:
            lines.append(f"        - Host: {consenter['Host']}")
            lines.append(f"          Port: {consenter['Port']}")
            lines.append(f"          ClientTLSCert: {consenter['ClientTLSCert']}")
            lines.append(f"          ServerTLSCert: {consenter['ServerTLSCert']}")
        lines.append(f"      Organizations:")
        lines.append(f"      - *{org_anchors['OrdererOrg']}")
        lines.append("      Policies:")
        for policy_name, policy in configtx['Orderer']['Policies'].items():
            lines.append(f"        {policy_name}:")
            lines.append(f"          Type: {policy['Type']}")
            lines.append(f"          Rule: {policy['Rule']}")
        lines.append("      Capabilities:")
        lines.append(f"        V2_0: {str(configtx['Orderer']['Capabilities']['V2_0']).lower()}")
        lines.append(f"      BatchTimeout: {configtx['Orderer']['BatchTimeout']}")
        lines.append("      BatchSize:")
        lines.append(f"        MaxMessageCount: {batch_size['MaxMessageCount']}")
        lines.append(f"        AbsoluteMaxBytes: {batch_size['AbsoluteMaxBytes']}")
        lines.append(f"        PreferredMaxBytes: {batch_size['PreferredMaxBytes']}")
        lines.append("    Consortiums:")
        lines.append("      SampleConsortium:")
        lines.append("        Organizations:")
        lines.append(f"        - *{org_anchors['Org1MSP']}")
        lines.append(f"        - *{org_anchors['Org2MSP']}")
        # Добавляем Channel Policies в профиль для генерации genesis блока
        lines.append("    Policies:")
        for policy_name, policy in configtx['Channel']['Policies'].items():
            lines.append(f"      {policy_name}:")
            lines.append(f"        Type: {policy['Type']}")
            lines.append(f"        Rule: {policy['Rule']}")
        lines.append("    Capabilities:")
        lines.append(f"      V2_0: {str(configtx['Channel']['Capabilities']['V2_0']).lower()}")
        lines.append("  TwoOrgsChannel:")
        lines.append("    Consortium: SampleConsortium")
        lines.append("    Application:")
        lines.append("      Organizations:")
        lines.append(f"      - *{org_anchors['Org1MSP']}")
        lines.append(f"      - *{org_anchors['Org2MSP']}")
        lines.append("      Policies:")
        for policy_name, policy in configtx['Application']['Policies'].items():
            lines.append(f"        {policy_name}:")
            lines.append(f"          Type: {policy['Type']}")
            lines.append(f"          Rule: {policy['Rule']}")
        lines.append("      Capabilities:")
        lines.append(f"        V2_0: {str(configtx['Application']['Capabilities']['V2_0']).lower()}")
        # Добавляем Orderer секцию в профиль канала для поддержки orderer endpoints
        if 'Orderer' in configtx['Profiles']['TwoOrgsChannel']:
            orderer_profile = configtx['Profiles']['TwoOrgsChannel']['Orderer']
            lines.append("    Orderer:")
            lines.append("      OrdererType: etcdraft")
            if 'Addresses' in orderer_profile:
                lines.append("      Addresses:")
                for addr in orderer_profile['Addresses']:
                    lines.append(f"      - {addr}")
            lines.append("      EtcdRaft:")
            lines.append("        Consenters:")
            for consenter in orderer_profile['EtcdRaft']['Consenters']:
                lines.append(f"        - Host: {consenter['Host']}")
                lines.append(f"          Port: {consenter['Port']}")
                lines.append(f"          ClientTLSCert: {consenter['ClientTLSCert']}")
                lines.append(f"          ServerTLSCert: {consenter['ServerTLSCert']}")
            lines.append("      Organizations:")
            lines.append(f"      - *{org_anchors['OrdererOrg']}")
            lines.append("      Policies:")
            for policy_name, policy in orderer_profile['Policies'].items():
                lines.append(f"        {policy_name}:")
                lines.append(f"          Type: {policy['Type']}")
                lines.append(f"          Rule: {policy['Rule']}")
            lines.append("      Capabilities:")
            lines.append(f"        V2_0: {str(orderer_profile['Capabilities']['V2_0']).lower()}")
            lines.append(f"      BatchTimeout: {orderer_profile['BatchTimeout']}")
            lines.append("      BatchSize:")
            batch_size = orderer_profile['BatchSize']
            lines.append(f"        MaxMessageCount: {batch_size['MaxMessageCount']}")
            lines.append(f"        AbsoluteMaxBytes: {batch_size['AbsoluteMaxBytes']}")
            lines.append(f"        PreferredMaxBytes: {batch_size['PreferredMaxBytes']}")
        # Добавляем Channel Policies в профиль для генерации транзакции создания канала
        lines.append("    Policies:")
        for policy_name, policy in configtx['Channel']['Policies'].items():
            lines.append(f"      {policy_name}:")
            lines.append(f"        Type: {policy['Type']}")
            lines.append(f"        Rule: {policy['Rule']}")
        lines.append("    Capabilities:")
        lines.append(f"      V2_0: {str(configtx['Channel']['Capabilities']['V2_0']).lower()}")
        
        # Записываем в файл
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def generate_docker_compose(self):
        """Генерирует docker-compose.yaml с CA серверами"""
        docker_compose = {
            'version': '3.8',
            'services': {
                'ca_orderer': {
                    'container_name': 'ca_orderer',
                    'image': 'hyperledger/fabric-ca:1.5',
                    'environment': [
                        'FABRIC_CA_HOME=/etc/hyperledger/fabric-ca-server',
                        'FABRIC_CA_SERVER_CA_NAME=ca-orderer',
                        'FABRIC_CA_SERVER_TLS_ENABLED=true',
                        'FABRIC_CA_SERVER_PORT=7054',
                        'FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS=0.0.0.0:9443'
                    ],
                    'ports': [
                        '7054:7054',
                        '9443:9443'
                    ],
                    'command': 'sh -c "fabric-ca-server start -b admin:adminpw -d"',
                    'volumes': [
                        './organizations/fabric-ca/ordererOrg:/etc/hyperledger/fabric-ca-server-config'
                    ],
                    'networks': [
                        'fabric-network'
                    ]
                },
                'ca_org1': {
                    'container_name': 'ca_org1',
                    'image': 'hyperledger/fabric-ca:1.5',
                    'environment': [
                        'FABRIC_CA_HOME=/etc/hyperledger/fabric-ca-server',
                        'FABRIC_CA_SERVER_CA_NAME=ca-org1',
                        'FABRIC_CA_SERVER_TLS_ENABLED=true',
                        'FABRIC_CA_SERVER_PORT=7054',
                        'FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS=0.0.0.0:9444'
                    ],
                    'ports': [
                        '7154:7054',
                        '9444:9444'
                    ],
                    'command': 'sh -c "fabric-ca-server start -b admin:adminpw -d"',
                    'volumes': [
                        './organizations/fabric-ca/org1:/etc/hyperledger/fabric-ca-server-config'
                    ],
                    'networks': [
                        'fabric-network'
                    ]
                },
                'ca_org2': {
                    'container_name': 'ca_org2',
                    'image': 'hyperledger/fabric-ca:1.5',
                    'environment': [
                        'FABRIC_CA_HOME=/etc/hyperledger/fabric-ca-server',
                        'FABRIC_CA_SERVER_CA_NAME=ca-org2',
                        'FABRIC_CA_SERVER_TLS_ENABLED=true',
                        'FABRIC_CA_SERVER_PORT=7054',
                        'FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS=0.0.0.0:9445'
                    ],
                    'ports': [
                        '8054:7054',
                        '9445:9445'
                    ],
                    'command': 'sh -c "fabric-ca-server start -b admin:adminpw -d"',
                    'volumes': [
                        './organizations/fabric-ca/org2:/etc/hyperledger/fabric-ca-server-config'
                    ],
                    'networks': [
                        'fabric-network'
                    ]
                },
                'orderer0': {
                    'container_name': 'orderer0',
                    'image': 'hyperledger/fabric-orderer:2.5',
                    'environment': [
                        'FABRIC_LOGGING_SPEC=INFO',
                        'ORDERER_GENERAL_LISTENADDRESS=0.0.0.0',
                        'ORDERER_GENERAL_LISTENPORT=7050',
                        'ORDERER_GENERAL_BOOTSTRAPMETHOD=file',
                        'ORDERER_GENERAL_BOOTSTRAPFILE=/var/hyperledger/orderer/orderer.genesis.block',
                        'ORDERER_GENERAL_LOCALMSPID=OrdererMSP',
                        'ORDERER_GENERAL_LOCALMSPDIR=/var/hyperledger/orderer/msp',
                        'ORDERER_GENERAL_TLS_ENABLED=true',
                        'ORDERER_GENERAL_TLS_PRIVATEKEY=/var/hyperledger/orderer/tls/server.key',
                        'ORDERER_GENERAL_TLS_CERTIFICATE=/var/hyperledger/orderer/tls/server.crt',
                        'ORDERER_GENERAL_TLS_ROOTCAS=[/var/hyperledger/orderer/tls/ca.crt]',
                        # Не требуем mutual TLS для peer-to-orderer соединений (стандартная конфигурация Fabric)
                        # Mutual TLS используется только для orderer-to-orderer кластерных соединений
                        'ORDERER_GENERAL_CLUSTER_CLIENTCERTIFICATE=/var/hyperledger/orderer/tls/server.crt',
                        'ORDERER_GENERAL_CLUSTER_CLIENTPRIVATEKEY=/var/hyperledger/orderer/tls/server.key',
                        'ORDERER_GENERAL_CLUSTER_ROOTCAS=[/var/hyperledger/orderer/tls/ca.crt]',
                        'ORDERER_KAFKA_TOPIC_REPLICATIONFACTOR=1',
                        'ORDERER_KAFKA_VERBOSE=true',
                        'ORDERER_GENERAL_GENESISMETHOD=file',
                        'ORDERER_GENERAL_GENESISFILE=/var/hyperledger/orderer/orderer.genesis.block',
                        'ORDERER_FILELEDGER_LOCATION=/var/hyperledger/production/orderer',
                        'ORDERER_GENERAL_GENESISPROFILE=TwoOrgsOrdererGenesis'
                    ],
                    'working_dir': '/opt/gopath/src/github.com/hyperledger/fabric',
                    'command': 'orderer',
                    'volumes': [
                        './channel-artifacts/genesis.block:/var/hyperledger/orderer/orderer.genesis.block',
                        './organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp:/var/hyperledger/orderer/msp',
                        './organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/:/var/hyperledger/orderer/tls',
                        'orderer0:/var/hyperledger/production/orderer'
                    ],
                    'ports': [
                        '7050:7050'
                    ],
                    'depends_on': [
                        'ca_orderer'
                    ],
                    'networks': {
                        'fabric-network': {
                            'aliases': [
                                'orderer.example.com'
                            ]
                        }
                    }
                },
                'peer0.org1.example.com': {
                    'container_name': 'peer0.org1.example.com',
                    'image': 'hyperledger/fabric-peer:2.5',
                    'environment': [
                        'CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock',
                        'CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=fabric-network',
                        'FABRIC_LOGGING_SPEC=INFO',
                        'CORE_PEER_TLS_ENABLED=true',
                        'CORE_PEER_PROFILE_ENABLED=true',
                        'CORE_PEER_TLS_CERT_FILE=/etc/hyperledger/fabric/tls/server.crt',
                        'CORE_PEER_TLS_KEY_FILE=/etc/hyperledger/fabric/tls/server.key',
                        'CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt',
                        'CORE_PEER_ID=peer0.org1.example.com',
                        'CORE_PEER_ADDRESS=peer0.org1.example.com:7051',
                        'CORE_PEER_LISTENADDRESS=0.0.0.0:7051',
                        'CORE_PEER_CHAINCODEADDRESS=peer0.org1.example.com:7052',
                        'CORE_PEER_CHAINCODELISTENADDRESS=0.0.0.0:7052',
                        'CORE_PEER_GOSSIP_BOOTSTRAP=peer0.org1.example.com:7051',
                        'CORE_PEER_GOSSIP_EXTERNALENDPOINT=peer0.org1.example.com:7051',
                        'CORE_PEER_LOCALMSPID=Org1MSP',
                        'CORE_OPERATIONS_LISTENADDRESS=0.0.0.0:8443',
                        'CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG={"peers":[{"name":"peer0.org1.example.com","address":"peer0.org1.example.com:7052","tls_required":true,"client_tls_cert":"/etc/hyperledger/fabric/peer/tls/ca.crt","root_cert":"/etc/hyperledger/fabric/peer/tls/ca.crt"}]}',
                        'CORE_PEER_EXTERNALBUILDERS=[{"name":"ccaas_builder","path":"/opt/hyperledger/ccaas_builder","propagateEnvironment":["CHAINCODE_AS_A_SERVICE"]}]',
                        'CORE_PEER_TLS_CLIENTAUTHREQUIRED=true',
                        'CORE_PEER_TLS_CLIENTROOTCAS_FILES=/etc/hyperledger/fabric/tls/ca.crt',
                        'CORE_PEER_TLS_CLIENTCERT_FILE=/etc/hyperledger/fabric/tls/server.crt',
                        'CORE_PEER_TLS_CLIENTKEY_FILE=/etc/hyperledger/fabric/tls/server.key',
                        'CORE_PEER_GOSSIP_USELEADERELECTION=true',
                        'CORE_PEER_GOSSIP_ORGLEADER=false',
                        'CORE_PEER_GOSSIP_SKIPHANDSHAKE=true',
                        'CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp',
                        'CORE_LEDGER_STATE_STATEDATABASE=CouchDB',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS=couchdb0:5984',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME=admin',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD=adminpw'
                    ],
                    'volumes': [
                        '/var/run/:/host/var/run/',
                        './organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/msp:/etc/hyperledger/fabric/msp',
                        './organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/:/etc/hyperledger/fabric/tls',
                        'peer0.org1.example.com:/var/hyperledger/production'
                    ],
                    'working_dir': '/opt/gopath/src/github.com/hyperledger/fabric/peer',
                    'command': 'peer node start',
                    'ports': [
                        '7051:7051',
                        '8443:8443'
                    ],
                    'depends_on': [
                        'orderer0',
                        'ca_org1',
                        'couchdb0'
                    ],
                    'networks': {
                        'fabric-network': {
                            'aliases': [
                                'peer0.org1.example.com'
                            ]
                        }
                    }
                },
                'couchdb0': {
                    'container_name': 'couchdb0',
                    'image': 'couchdb:3.2',
                    'environment': [
                        'COUCHDB_USER=admin',
                        'COUCHDB_PASSWORD=adminpw'
                    ],
                    'ports': [
                        '5984:5984'
                    ],
                    'networks': [
                        'fabric-network'
                    ]
                },
                'peer0.org2.example.com': {
                    'container_name': 'peer0.org2.example.com',
                    'image': 'hyperledger/fabric-peer:2.5',
                    'environment': [
                        'CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock',
                        'CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=fabric-network',
                        'FABRIC_LOGGING_SPEC=INFO',
                        'CORE_PEER_TLS_ENABLED=true',
                        'CORE_PEER_PROFILE_ENABLED=true',
                        'CORE_PEER_TLS_CERT_FILE=/etc/hyperledger/fabric/tls/server.crt',
                        'CORE_PEER_TLS_KEY_FILE=/etc/hyperledger/fabric/tls/server.key',
                        'CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt',
                        'CORE_PEER_ID=peer0.org2.example.com',
                        'CORE_PEER_ADDRESS=peer0.org2.example.com:9051',
                        'CORE_PEER_LISTENADDRESS=0.0.0.0:9051',
                        'CORE_PEER_CHAINCODEADDRESS=peer0.org2.example.com:9052',
                        'CORE_PEER_CHAINCODELISTENADDRESS=0.0.0.0:9052',
                        'CORE_PEER_GOSSIP_BOOTSTRAP=peer0.org2.example.com:9051',
                        'CORE_PEER_GOSSIP_EXTERNALENDPOINT=peer0.org2.example.com:9051',
                        'CORE_PEER_LOCALMSPID=Org2MSP',
                        'CORE_OPERATIONS_LISTENADDRESS=0.0.0.0:8444',
                        'CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG={"peers":[{"name":"peer0.org2.example.com","address":"peer0.org2.example.com:9052","tls_required":true,"client_tls_cert":"/etc/hyperledger/fabric/peer/tls/ca.crt","root_cert":"/etc/hyperledger/fabric/peer/tls/ca.crt"}]}',
                        'CORE_PEER_EXTERNALBUILDERS=[{"name":"ccaas_builder","path":"/opt/hyperledger/ccaas_builder","propagateEnvironment":["CHAINCODE_AS_A_SERVICE"]}]',
                        'CORE_PEER_TLS_CLIENTAUTHREQUIRED=true',
                        'CORE_PEER_TLS_CLIENTROOTCAS_FILES=/etc/hyperledger/fabric/tls/ca.crt',
                        'CORE_PEER_TLS_CLIENTCERT_FILE=/etc/hyperledger/fabric/tls/server.crt',
                        'CORE_PEER_TLS_CLIENTKEY_FILE=/etc/hyperledger/fabric/tls/server.key',
                        'CORE_PEER_GOSSIP_USELEADERELECTION=true',
                        'CORE_PEER_GOSSIP_ORGLEADER=false',
                        'CORE_PEER_GOSSIP_SKIPHANDSHAKE=true',
                        'CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp',
                        'CORE_LEDGER_STATE_STATEDATABASE=CouchDB',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS=couchdb1:5984',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME=admin',
                        'CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD=adminpw'
                    ],
                    'volumes': [
                        '/var/run/:/host/var/run/',
                        './organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/msp:/etc/hyperledger/fabric/msp',
                        './organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/:/etc/hyperledger/fabric/tls',
                        'peer0.org2.example.com:/var/hyperledger/production'
                    ],
                    'working_dir': '/opt/gopath/src/github.com/hyperledger/fabric/peer',
                    'command': 'peer node start',
                    'ports': [
                        '9051:9051',
                        '8444:8444'
                    ],
                    'depends_on': [
                        'orderer0',
                        'ca_org2',
                        'couchdb1'
                    ],
                    'networks': {
                        'fabric-network': {
                            'aliases': [
                                'peer0.org2.example.com'
                            ]
                        }
                    }
                },
                'couchdb1': {
                    'container_name': 'couchdb1',
                    'image': 'couchdb:3.2',
                    'environment': [
                        'COUCHDB_USER=admin',
                        'COUCHDB_PASSWORD=adminpw'
                    ],
                    'ports': [
                        '5985:5984'
                    ],
                    'networks': [
                        'fabric-network'
                    ]
                }
            },
            'networks': {
                'fabric-network': {
                    'driver': 'bridge'
                }
            },
            'volumes': {
                'orderer0': None,
                'peer0.org1.example.com': None,
                'peer0.org2.example.com': None
            }
        }
        
        compose_path = self.base_dir / "docker-compose.yaml"
        with open(compose_path, 'w', encoding='utf-8') as f:
            yaml.dump(docker_compose, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"✓ Создан файл: {compose_path}")
        return compose_path
    
    def generate_all(self):
        """Генерирует всю конфигурацию"""
        print("=" * 60)
        print("Генерация конфигурации Hyperledger Fabric v2.x")
        print("=" * 60)
        
        self.create_directories()
        self.generate_crypto_config()
        self.generate_configtx()
        self.generate_docker_compose()
        
        print("\n" + "=" * 60)
        print("✓ Конфигурация успешно создана!")
        print("=" * 60)
        print("\nСледующие шаги:")
        print("1. Установите инструменты Hyperledger Fabric (cryptogen, configtxgen)")
        print("2. Запустите network_setup.py для инструкций по генерации артефактов")
        print("3. Используйте docker-compose up -d для запуска сети")


def main():
    generator = FabricConfigGenerator()
    generator.generate_all()


if __name__ == "__main__":
    main()

