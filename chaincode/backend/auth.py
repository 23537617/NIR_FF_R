#!/usr/bin/env python3
"""
Модуль авторизации и проверки ролей
Реализует проверку прав доступа для различных ролей пользователей
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status, Header, Depends
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """Роли пользователей"""
    JURIST = "юрист"  # Юрист
    EXPERT = "эксперт"  # Эксперт
    MODERATOR = "модератор"  # Модератор
    ADMIN = "admin"  # Администратор (полный доступ)


class Permission(str, Enum):
    """Разрешения для операций"""
    ADD_DOCUMENT_VERSION = "add_document_version"  # Добавление версий документа
    CONFIRM_TASK = "confirm_task"  # Подтверждение задач
    UPDATE_TASK_STATUS = "update_task_status"  # Обновление статусов задач
    CREATE_TASK = "create_task"  # Создание задач
    VIEW_TASK = "view_task"  # Просмотр задач
    VIEW_DOCUMENTS = "view_documents"  # Просмотр документов


# Маппинг ролей на разрешения
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.JURIST: [
        Permission.ADD_DOCUMENT_VERSION,
        Permission.VIEW_TASK,
        Permission.VIEW_DOCUMENTS
    ],
    UserRole.EXPERT: [
        Permission.CONFIRM_TASK,
        Permission.VIEW_TASK,
        Permission.VIEW_DOCUMENTS
    ],
    UserRole.MODERATOR: [
        Permission.UPDATE_TASK_STATUS,
        Permission.VIEW_TASK,
        Permission.VIEW_DOCUMENTS
    ],
    UserRole.ADMIN: [
        Permission.CREATE_TASK,
        Permission.UPDATE_TASK_STATUS,
        Permission.ADD_DOCUMENT_VERSION,
        Permission.CONFIRM_TASK,
        Permission.VIEW_TASK,
        Permission.VIEW_DOCUMENTS
    ]
}


def has_permission(user_role: UserRole, permission: Permission) -> bool:
    """
    Проверить, имеет ли роль указанное разрешение
    
    Args:
        user_role: Роль пользователя
        permission: Требуемое разрешение
    
    Returns:
        True если разрешение есть, False иначе
    """
    if user_role == UserRole.ADMIN:
        return True  # Администратор имеет все права
    
    role_permissions = ROLE_PERMISSIONS.get(user_role, [])
    return permission in role_permissions


def get_user_role_from_header(x_user_role: Optional[str] = Header(None, alias="X-User-Role")) -> Optional[UserRole]:
    """
    Получить роль пользователя из заголовка запроса
    
    Args:
        x_user_role: Роль пользователя из заголовка X-User-Role
    
    Returns:
        UserRole или None
    """
    if not x_user_role:
        return None
    
    try:
        # Нормализация роли (приведение к нижнему регистру)
        role_lower = x_user_role.lower().strip()
        
        # Маппинг русских названий на enum
        role_mapping = {
            "юрист": UserRole.JURIST,
            "jurist": UserRole.JURIST,
            "эксперт": UserRole.EXPERT,
            "expert": UserRole.EXPERT,
            "модератор": UserRole.MODERATOR,
            "moderator": UserRole.MODERATOR,
            "admin": UserRole.ADMIN,
            "администратор": UserRole.ADMIN
        }
        
        return role_mapping.get(role_lower)
    
    except Exception as e:
        logger.warning(f"Ошибка парсинга роли: {str(e)}")
        return None


def require_permission(permission: Permission):
    """
    Декоратор для проверки разрешения
    
    Args:
        permission: Требуемое разрешение
    
    Returns:
        Dependency функция для FastAPI
    """
    def permission_checker(user_role: Optional[UserRole] = Depends(get_user_role_from_header)):
        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Роль пользователя не указана. Укажите заголовок X-User-Role"
            )
        
        if not has_permission(user_role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Роль '{user_role.value}' не имеет разрешения на выполнение этой операции. "
                       f"Требуется разрешение: {permission.value}"
            )
        
        return user_role
    
    return permission_checker


def require_role(allowed_roles: List[UserRole]):
    """
    Проверка, что пользователь имеет одну из указанных ролей
    
    Args:
        allowed_roles: Список разрешенных ролей
    
    Returns:
        Dependency функция для FastAPI
    """
    def role_checker(user_role: Optional[UserRole] = Depends(get_user_role_from_header)):
        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Роль пользователя не указана. Укажите заголовок X-User-Role"
            )
        
        if user_role not in allowed_roles:
            allowed_roles_str = ", ".join([r.value for r in allowed_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Доступ запрещен. Разрешенные роли: {allowed_roles_str}. "
                       f"Ваша роль: {user_role.value}"
            )
        
        return user_role
    
    return role_checker


def get_user_info(user_role: Optional[UserRole] = Depends(get_user_role_from_header)) -> Dict[str, Any]:
    """
    Получить информацию о пользователе и его разрешениях
    
    Args:
        user_role: Роль пользователя
    
    Returns:
        Словарь с информацией о пользователе
    """
    if user_role is None:
        return {
            "role": None,
            "permissions": [],
            "authenticated": False
        }
    
    permissions = ROLE_PERMISSIONS.get(user_role, [])
    
    return {
        "role": user_role.value,
        "permissions": [p.value for p in permissions],
        "authenticated": True
    }



