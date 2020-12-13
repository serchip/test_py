# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Session
from app.connects.postgres.base import DBBase


class User(DBBase):
    """Модель пользователя
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    """int: primary_key"""
    username = Column(String, unique=True, index=True)
    """str: логин пользователя"""
    is_active = Column(Boolean, default=False)
    """str: акнивен/не активен пользователь"""
    balance = relationship("Balance", uselist=False, back_populates="user")
