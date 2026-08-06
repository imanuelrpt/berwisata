from typing import Any, Generic, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, obj_id: int) -> Optional[ModelType]:
        return self.db.get(self.model, obj_id)

    def get_by(self, **kwargs) -> Optional[ModelType]:
        stmt = select(self.model).filter_by(**kwargs)
        return self.db.scalars(stmt).first()

    def list(self, offset: int = 0, limit: int = 50) -> list[ModelType]:
        stmt = select(self.model).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count(self, **filters) -> int:
        stmt = select(func.count(self.model.id))
        for k, v in filters.items():
            stmt = stmt.where(getattr(self.model, k) == v)
        return int(self.db.scalar(stmt) or 0)

    def create(self, data: CreateSchemaType, commit: bool = True) -> ModelType:
        obj = self.model(**data.model_dump(exclude_unset=True))
        self.db.add(obj)
        if commit:
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def create_raw(self, **values: Any) -> ModelType:
        obj = self.model(**values)
        self.db.add(obj)
        return obj

    def update(self, obj: ModelType, data: UpdateSchemaType, commit: bool = True) -> ModelType:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        if commit:
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def update_fields(self, obj: ModelType, commit: bool = True, **values: Any) -> ModelType:
        for field, value in values.items():
            setattr(obj, field, value)
        if commit:
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType, commit: bool = True) -> None:
        self.db.delete(obj)
        if commit:
            self.db.commit()
