from typing import Optional
from sqlalchemy.orm import Session, joinedload

from app.database.models import (
    BudgetCategoryModel,
    ChatMessageModel,
    ChatSessionModel,
    EventModel,
    ExpenseModel,
    KnowledgeDocumentModel,
    TaskModel,
    utcnow,
)


class EventRepository:
    @staticmethod
    def list_events(db: Session, skip: int = 0, limit: int = 50) -> list[EventModel]:
        return (
            db.query(EventModel)
            .options(
                joinedload(EventModel.budget_categories),
                joinedload(EventModel.expenses),
                joinedload(EventModel.tasks),
            )
            .order_by(EventModel.event_date.asc(), EventModel.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_event(db: Session, event_id: int) -> Optional[EventModel]:
        return (
            db.query(EventModel)
            .options(
                joinedload(EventModel.budget_categories),
                joinedload(EventModel.expenses),
                joinedload(EventModel.tasks),
            )
            .filter(EventModel.id == event_id)
            .first()
        )

    @staticmethod
    def create_event(db: Session, event_obj: EventModel) -> EventModel:
        db.add(event_obj)
        db.flush()
        return event_obj

    @staticmethod
    def delete_event(db: Session, event_obj: EventModel) -> None:
        db.delete(event_obj)
        db.commit()


class BudgetRepository:
    @staticmethod
    def replace_categories(
        db: Session,
        event_id: int,
        categories: list[BudgetCategoryModel],
    ) -> list[BudgetCategoryModel]:
        db.query(BudgetCategoryModel).filter(BudgetCategoryModel.event_id == event_id).delete(
            synchronize_session="fetch"
        )
        for cat in categories:
            cat.event_id = event_id
            db.add(cat)
        db.flush()
        return categories

    @staticmethod
    def add_expense(db: Session, expense: ExpenseModel) -> ExpenseModel:
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense

    @staticmethod
    def get_expense(db: Session, expense_id: int, event_id: int) -> Optional[ExpenseModel]:
        return (
            db.query(ExpenseModel)
            .filter(ExpenseModel.id == expense_id, ExpenseModel.event_id == event_id)
            .first()
        )

    @staticmethod
    def delete_expense(db: Session, expense: ExpenseModel) -> None:
        db.delete(expense)
        db.commit()


class TaskRepository:
    @staticmethod
    def replace_tasks_for_event(
        db: Session,
        event_id: int,
        tasks: list[TaskModel],
        preserve_completed: bool = True,
    ) -> list[TaskModel]:
        existing = db.query(TaskModel).filter(TaskModel.event_id == event_id).all()
        completed_map = {}
        if preserve_completed:
            for t in existing:
                if t.status in ("completed", "in_progress"):
                    completed_map[t.title.lower().strip()] = t.status

        db.query(TaskModel).filter(TaskModel.event_id == event_id).delete(synchronize_session="fetch")
        for task in tasks:
            task.event_id = event_id
            preserved_status = completed_map.get(task.title.lower().strip())
            if preserved_status:
                task.status = preserved_status
            db.add(task)
        db.flush()
        return tasks

    @staticmethod
    def list_tasks_for_event(db: Session, event_id: int) -> list[TaskModel]:
        return (
            db.query(TaskModel)
            .filter(TaskModel.event_id == event_id)
            .order_by(TaskModel.due_date.asc(), TaskModel.id.asc())
            .all()
        )

    @staticmethod
    def get_task(db: Session, task_id: int) -> Optional[TaskModel]:
        return db.query(TaskModel).filter(TaskModel.id == task_id).first()

    @staticmethod
    def create_task(db: Session, task: TaskModel) -> TaskModel:
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task: TaskModel) -> None:
        db.delete(task)
        db.commit()


class ChatRepository:
    @staticmethod
    def get_or_create_session(
        db: Session,
        session_id: Optional[int] = None,
        event_id: Optional[int] = None,
        title: str = "Event Planning Assistant",
    ) -> ChatSessionModel:
        if session_id is not None:
            session = db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()
            if session:
                if event_id is not None and session.event_id != event_id:
                    session.event_id = event_id
                session.updated_at = utcnow()
                db.flush()
                return session

        if event_id is not None:
            existing_for_event = (
                db.query(ChatSessionModel)
                .filter(ChatSessionModel.event_id == event_id)
                .order_by(ChatSessionModel.updated_at.desc())
                .first()
            )
            if existing_for_event and session_id is None:
                return existing_for_event

        new_session = ChatSessionModel(event_id=event_id, title=title)
        db.add(new_session)
        db.flush()
        return new_session

    @staticmethod
    def add_message(db: Session, msg: ChatMessageModel) -> ChatMessageModel:
        db.add(msg)
        db.flush()
        return msg

    @staticmethod
    def list_sessions(db: Session, event_id: Optional[int] = None) -> list[ChatSessionModel]:
        query = db.query(ChatSessionModel).options(joinedload(ChatSessionModel.messages))
        if event_id is not None:
            query = query.filter(ChatSessionModel.event_id == event_id)
        return query.order_by(ChatSessionModel.updated_at.desc()).limit(25).all()

    @staticmethod
    def get_session(db: Session, session_id: int) -> Optional[ChatSessionModel]:
        return (
            db.query(ChatSessionModel)
            .options(joinedload(ChatSessionModel.messages))
            .filter(ChatSessionModel.id == session_id)
            .first()
        )


class KnowledgeRepository:
    @staticmethod
    def list_documents(db: Session) -> list[KnowledgeDocumentModel]:
        return (
            db.query(KnowledgeDocumentModel)
            .order_by(KnowledgeDocumentModel.updated_at.desc())
            .all()
        )

    @staticmethod
    def get_document(db: Session, document_id: str) -> Optional[KnowledgeDocumentModel]:
        return (
            db.query(KnowledgeDocumentModel)
            .filter(KnowledgeDocumentModel.id == document_id)
            .first()
        )

    @staticmethod
    def upsert_document(db: Session, doc: KnowledgeDocumentModel) -> KnowledgeDocumentModel:
        existing = KnowledgeRepository.get_document(db, doc.id)
        if existing:
            existing.title = doc.title
            existing.filename = doc.filename
            existing.file_type = doc.file_type
            existing.file_path = doc.file_path
            existing.raw_content = doc.raw_content
            existing.event_type = doc.event_type
            existing.category = doc.category
            existing.location = doc.location
            existing.source_label = doc.source_label
            existing.is_illustrative = doc.is_illustrative
            existing.status = doc.status
            existing.chunk_count = doc.chunk_count
            existing.error_message = doc.error_message
            existing.updated_at = utcnow()
            db.commit()
            db.refresh(existing)
            return existing
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def delete_document(db: Session, doc: KnowledgeDocumentModel) -> None:
        db.delete(doc)
        db.commit()
