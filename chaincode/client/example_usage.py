#!/usr/bin/env python3
"""
Примеры использования Fabric SDK клиента
"""

import json
from client import ChaincodeClient


def example_create_task(client: ChaincodeClient):
    """Пример создания задачи"""
    print("\n=== Создание задачи ===")
    
    result = client.create_task(
        task_id="TASK001",
        title="Разработка новой функции",
        description="Реализовать новую функцию в chaincode",
        assignee="developer1",
        creator="admin"
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def example_get_task(client: ChaincodeClient, task_id: str):
    """Пример получения задачи"""
    print(f"\n=== Получение задачи {task_id} ===")
    
    result = client.get_task(task_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def example_update_status(client: ChaincodeClient, task_id: str):
    """Пример обновления статуса"""
    print(f"\n=== Обновление статуса задачи {task_id} ===")
    
    result = client.update_task_status(
        task_id=task_id,
        new_status="IN_PROGRESS",
        updated_by="developer1"
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def example_add_document(client: ChaincodeClient, task_id: str):
    """Пример добавления версии документа"""
    print(f"\n=== Добавление версии документа для задачи {task_id} ===")
    
    result = client.add_document_version(
        task_id=task_id,
        document_id="DOC001",
        version="1.0",
        content_hash="sha256:abc123def456...",
        uploaded_by="developer1",
        metadata={
            "filename": "specification.pdf",
            "size": 2048,
            "mime_type": "application/pdf",
            "upload_date": "2024-01-15T10:30:00Z"
        }
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def example_get_versions(client: ChaincodeClient, task_id: str, document_id: str):
    """Пример получения версий документа"""
    print(f"\n=== Получение версий документа {document_id} для задачи {task_id} ===")
    
    result = client.get_document_versions(task_id, document_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def example_workflow(client: ChaincodeClient):
    """Полный пример workflow"""
    print("\n" + "="*60)
    print("Полный пример workflow")
    print("="*60)
    
    # 1. Создание задачи
    create_result = example_create_task(client)
    if not create_result.get("success"):
        print("Ошибка при создании задачи")
        return
    
    task_id = "TASK001"
    
    # 2. Получение задачи
    example_get_task(client, task_id)
    
    # 3. Обновление статуса
    example_update_status(client, task_id)
    
    # 4. Добавление документа
    example_add_document(client, task_id)
    
    # 5. Добавление еще одной версии документа
    print(f"\n=== Добавление версии 2.0 документа ===")
    client.add_document_version(
        task_id=task_id,
        document_id="DOC001",
        version="2.0",
        content_hash="sha256:xyz789ghi012...",
        uploaded_by="developer2",
        metadata={
            "filename": "specification_v2.pdf",
            "size": 3072,
            "changes": "Обновлена спецификация"
        }
    )
    
    # 6. Получение всех версий
    example_get_versions(client, task_id, "DOC001")
    
    # 7. Завершение задачи
    print(f"\n=== Завершение задачи {task_id} ===")
    client.update_task_status(task_id, "COMPLETED", "developer1")
    
    # 8. Финальное получение задачи
    example_get_task(client, task_id)


def main():
    """Главная функция"""
    # Инициализация клиента
    client = ChaincodeClient(
        connection_profile_path="connection-org1.json",
        channel_name="npa-channel",
        chaincode_name="taskdocument",
        org_name="Org1",
        user_name="Admin"
    )
    
    # Запуск примеров
    try:
        example_workflow(client)
    except Exception as e:
        print(f"\n❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()



