"""
db_utils.py
====================================
Утилиты для работы с базами данных
"""
from typing import List, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import ClauseElement


def get_or_create(session: Session, model: Any, defaults:dict = None, **kwargs)-> Tuple[Any, bool]:
    """
    Отдает или создает запись в БД
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        session.commit()
        return instance, True

def insert_or_update(session: Session, model: Any, defaults:dict = None, **kwargs)-> Tuple[Any, bool]:
    """
    Создать или обновить запись в БД
    """
    params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
    params.update(defaults or {})
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**params)
        session.add(instance)
    else:
        for k, v in defaults.items():
            if hasattr(instance, k):
                setattr(instance, k, v)
        session.merge(instance)
    session.commit()
    return True

row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}
