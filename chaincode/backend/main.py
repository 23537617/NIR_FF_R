#!/usr/bin/env python3
"""
FastAPI Backend для работы с Hyperledger Fabric Chaincode
Предоставляет REST API для вызова функций chaincode
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from pathlib import Path
from typing import Optional

try:
    from models import (
        CreateTaskRequest,
        UpdateTaskStatusRequest,
        AddDocumentVersionRequest,
        TaskResponse,
        DocumentVersionsResponse,
        ErrorResponse,
        SuccessResponse,
        ConfirmTaskRequest
    )
    from dependencies import get_chaincode_client
    from auth import (
        require_permission,
        require_role,
        Permission,
        UserRole,
        get_user_info
    )
except ImportError:
    # Для запуска как модуля
    from .models import (
        CreateTaskRequest,
        UpdateTaskStatusRequest,
        AddDocumentVersionRequest,
        TaskResponse,
        DocumentVersionsResponse,
        ErrorResponse,
        SuccessResponse,
        ConfirmTaskRequest
    )
    from .dependencies import get_chaincode_client
    from .auth import (
        require_permission,
        require_role,
        Permission,
        UserRole,
        get_user_info
    )

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="NPA Chaincode API",
    description="REST API для работы с Hyperledger Fabric Chaincode",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """Проверка работоспособности API"""
    return {
        "status": "healthy",
        "service": "NPA Chaincode API",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post(
    "/task/create",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
    summary="Создать задачу",
    description="Создает новую задачу в Hyperledger Fabric ledger. Требуется роль: admin"
)
async def create_task(
    request: CreateTaskRequest,
    client=Depends(get_chaincode_client),
    user_role=Depends(require_permission(Permission.CREATE_TASK))
):
    """
    Создать новую задачу
    
    Вызывает chaincode функцию: createTask
    """
    try:
        logger.info(f"Создание задачи: {request.task_id}")
        
        result = client.create_task(
            task_id=request.task_id,
            title=request.title,
            description=request.description,
            assignee=request.assignee,
            creator=request.creator
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Ошибка при создании задачи")
            )
        
        task_data = result.get("data", {}).get("task", {})
        return TaskResponse(
            success=True,
            task=task_data,
            message="Задача успешно создана"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании задачи: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@app.post(
    "/task/status/update",
    response_model=TaskResponse,
    tags=["Tasks"],
    summary="Обновить статус задачи",
    description="Обновляет статус существующей задачи. Требуется роль: модератор"
)
async def update_task_status(
    request: UpdateTaskStatusRequest,
    client=Depends(get_chaincode_client),
    user_role=Depends(require_permission(Permission.UPDATE_TASK_STATUS))
):
    """
    Обновить статус задачи
    
    Вызывает chaincode функцию: updateTaskStatus
    """
    try:
        logger.info(f"Обновление статуса задачи {request.task_id} на {request.status}")
        
        result = client.update_task_status(
            task_id=request.task_id,
            new_status=request.status,
            updated_by=request.updated_by
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Ошибка при обновлении статуса задачи")
            )
        
        task_data = result.get("data", {}).get("task", {})
        return TaskResponse(
            success=True,
            task=task_data,
            message="Статус задачи успешно обновлен"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса задачи: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@app.post(
    "/document/addVersion",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
    summary="Добавить версию документа",
    description="Добавляет новую версию документа к задаче. Требуется роль: юрист"
)
async def add_document_version(
    request: AddDocumentVersionRequest,
    client=Depends(get_chaincode_client),
    user_role=Depends(require_permission(Permission.ADD_DOCUMENT_VERSION))
):
    """
    Добавить версию документа
    
    Вызывает chaincode функцию: addDocumentVersion
    """
    try:
        logger.info(f"Добавление версии {request.version} документа {request.document_id} к задаче {request.task_id}")
        
        result = client.add_document_version(
            task_id=request.task_id,
            document_id=request.document_id,
            version=request.version,
            content_hash=request.content_hash,
            uploaded_by=request.uploaded_by,
            metadata=request.metadata
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Ошибка при добавлении версии документа")
            )
        
        task_data = result.get("data", {}).get("task", {})
        return TaskResponse(
            success=True,
            task=task_data,
            message="Версия документа успешно добавлена"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при добавлении версии документа: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@app.get(
    "/document/versions/{doc_id}",
    response_model=DocumentVersionsResponse,
    tags=["Documents"],
    summary="Получить версии документа",
    description="Получает все версии документа по ID документа. Требуется разрешение на просмотр документов"
)
async def get_document_versions(
    doc_id: str,
    task_id: str,
    client=Depends(get_chaincode_client),
    user_role=Depends(require_permission(Permission.VIEW_DOCUMENTS))
):
    """
    Получить все версии документа
    
    Вызывает chaincode функцию: getDocumentVersions
    
    Args:
        doc_id: Идентификатор документа
        task_id: Идентификатор задачи (query параметр)
    """
    try:
        logger.info(f"Получение версий документа {doc_id} для задачи {task_id}")
        
        result = client.get_document_versions(
            task_id=task_id,
            document_id=doc_id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Документ не найден")
            )
        
        data = result.get("data", {})
        return DocumentVersionsResponse(
            success=True,
            task_id=data.get("task_id"),
            document_id=data.get("document_id"),
            versions=data.get("versions", []),
            total_versions=data.get("total_versions", 0),
            message="Версии документа успешно получены"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении версий документа: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@app.get(
    "/task/{task_id}",
    response_model=TaskResponse,
    tags=["Tasks"],
    summary="Получить задачу",
    description="Получает задачу по ID. Требуется разрешение на просмотр задач"
)
async def get_task(
    task_id: str,
    client=Depends(get_chaincode_client),
    user_role=Depends(require_permission(Permission.VIEW_TASK))
):
    """
    Получить задачу по ID
    
    Вызывает chaincode функцию: getTask
    """
    try:
        logger.info(f"Получение задачи {task_id}")
        
        result = client.get_task(task_id=task_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Задача не найдена")
            )
        
        task_data = result.get("data", {}).get("task", {})
        return TaskResponse(
            success=True,
            task=task_data,
            message="Задача успешно получена"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении задачи: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@app.post(
    "/task/confirm",
    response_model=TaskResponse,
    tags=["Tasks"],
    summary="Подтвердить задачу",
    description="Подтверждает задачу экспертом. Требуется роль: эксперт"
)
async def confirm_task(
    request: ConfirmTaskRequest,
    client=Depends(get_chaincode_client),
    user_role=Depends(require_permission(Permission.CONFIRM_TASK))
):
    """
    Подтвердить задачу экспертом
    
    Вызывает chaincode функцию: updateTaskStatus со статусом CONFIRMED
    """
    try:
        logger.info(f"Подтверждение задачи {request.task_id} экспертом")
        
        # Подтверждение задачи - это обновление статуса на CONFIRMED
        result = client.update_task_status(
            task_id=request.task_id,
            new_status="CONFIRMED",
            updated_by=request.confirmed_by
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Ошибка при подтверждении задачи")
            )
        
        task_data = result.get("data", {}).get("task", {})
        return TaskResponse(
            success=True,
            task=task_data,
            message="Задача успешно подтверждена экспертом"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при подтверждении задачи: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@app.get(
    "/auth/user-info",
    tags=["Auth"],
    summary="Информация о пользователе",
    description="Получает информацию о текущем пользователе и его разрешениях"
)
async def get_user_info_endpoint(
    user_info: Dict[str, Any] = Depends(get_user_info)
):
    """Получить информацию о пользователе"""
    return user_info


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик исключений"""
    logger.error(f"Необработанное исключение: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Внутренняя ошибка сервера",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

