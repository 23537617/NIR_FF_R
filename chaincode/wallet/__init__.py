"""
Fabric Wallet Module
Модуль для создания и управления Fabric identity в локальном wallet
"""

from .wallet import (
    FabricWallet,
    get_wallet,
    create_identity,
    get_identity,
    list_identities
)

from .ca_helper import (
    load_certificate_from_fabric_org,
    create_identity_from_fabric_user
)

__all__ = [
    "FabricWallet",
    "get_wallet",
    "create_identity",
    "get_identity",
    "list_identities",
    "load_certificate_from_fabric_org",
    "create_identity_from_fabric_user"
]

__version__ = "1.0.0"

