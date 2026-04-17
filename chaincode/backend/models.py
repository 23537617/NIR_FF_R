#!/usr/bin/env python3
"""
Pydantic модели для FastAPI
Определяет структуру запросов и ответов
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List


class CreateTaskRequest(BaseModel):
    """Модель запроса для создания задачи"""
    task_id: str = Field(..., description="Уникальный идентификатор задачи", min_length=1)
    title: str = Field(..., description="Название задачи", min_length=1)
    description: str = Field(..., description="Описание задачи")
    assignee: str = Field(..., description="Исполнитель задачи", min_length=1)
    creator: str = Field(..., description="Создатель задачи", min_length=1)
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "TASK001",
                "title": "Разработка новой функции",
                "description": "Реализовать новую функцию в chaincode",
                "assignee": "developer1",
                "creator": "admin"
            }
        }


class UpdateTaskStatusRequest(BaseModel):
    """Модель запроса для обновления статуса задачи"""
    task_id: str = Field(..., description="Идентификатор задачи", min_length=1)
    status: str = Field(..., description="Новый статус задачи")
    updated_by: str = Field(..., description="Пользователь, обновивший статус", min_length=1)
    
    @validator("status")
    def validate_status(cls, v):
        """Валидация статуса"""
        valid_statuses = ["CREATED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "CONFIRMED"]
        if v.upper() not in valid_statuses:
            raise ValueError(f"Статус должен быть одним из: {', '.join(valid_statuses)}")
        return v.upper()
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "TASK001",
                "status": "IN_PROGRESS",
                "updated_by": "developer1"
            }
        }


class AddDocumentVersionRequest(BaseModel):
    """Модель запроса для добавления версии документа"""
    task_id: str = Field(..., description="Идентификатор задачи", min_length=1)
    document_id: str = Field(..., description="Идентификатор документа", min_length=1)
    version: str = Field(..., description="Версия документа (например, 1.0, 2.0)", min_length=1)
    content_hash: str = Field(..., description="Хеш содержимого документа", min_length=1)
    uploaded_by: str = Field(..., description="Пользователь, загрузивший документ", min_length=1)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Дополнительные метаданные документа")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "TASK001",
                "document_id": "DOC001",
                "version": "1.0",
                "content_hash": "sha256:abc123def456...",
                "uploaded_by": "developer1",
                "metadata": {
                    "filename": "specification.pdf",
                    "size": 2048,
                    "mime_type": "application/pdf"
                }
            }
        }


class TaskData(BaseModel):
    """Модель данных задачи"""
    task_id: str
    title: str
    description: str
    assignee: str
    creator: str
    status: str
    created_at: str
    updated_at: str
    documents: Optional[List[Dict[str, Any]]] = None
    updated_by: Optional[str] = None


class TaskResponse(BaseModel):
    """Модель ответа для операций с задачами"""
    success: bool
    task: TaskData
    message: str


class DocumentVersion(BaseModel):
    """Модель версии документа"""
    document_id: str
    version: str
    content_hash: str
    uploaded_by: str
    uploaded_at: str
    metadata: Optional[Dict[str, Any]] = None


class DocumentVersionsResponse(BaseModel):
    """Модель ответа для получения версий документа"""
    success: bool
    task_id: str
    document_id: str
    versions: List[Dict[str, Any]]
    total_versions: int
    message: str


class SuccessResponse(BaseModel):
    """Модель успешного ответа"""
    success: bool = True
    message: str


class ConfirmTaskRequest(BaseModel):
    """Модель запроса для подтверждения задачи экспертом"""
    task_id: str = Field(..., description="Идентификатор задачи", min_length=1)
    confirmed_by: str = Field(..., description="Эксперт, подтвердивший задачу", min_length=1)
    comment: Optional[str] = Field(None, description="Комментарий эксперта")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "TASK001",
                "confirmed_by": "expert1",
                "comment": "Задача соответствует требованиям"
            }
        }


class ErrorResponse(BaseModel):
    """Модель ответа с ошибкой"""
    success: bool = False
    error: str
    detail: Optional[str] = None

