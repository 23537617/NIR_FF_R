"""
IPFS Module
Модуль для работы с IPFS (InterPlanetary File System)
"""

from .ipfs_client import (
    IPFSClient,
    get_ipfs_client,
    upload_document,
    download_document
)

__all__ = [
    "IPFSClient",
    "get_ipfs_client",
    "upload_document",
    "download_document"
]

__version__ = "1.0.0"



