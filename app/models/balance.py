import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.connects.postgres.base import DBBase
from app.models.auth import User
from app.utils.db_utils import get_or_create


class Сurrency(enum.Enum):
    USD = 1

class Balance(DBBase):
    """Модель баланс пользователя
    """
    __tablename__ = "balances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="balance")
    amount = Column(Numeric, nullable=False, default=0)
    currency = Column(Enum(Сurrency), nullable=False, default=Сurrency.USD)

    @classmethod
    def get_system_balance(cls, db_session):
        db_user, _ = get_or_create(db_session, User, defaults={"is_active": False}, username='system_user')
        db_balance, _ = get_or_create(db_session, cls, user_id=db_user.id)
        return db_balance

    def set_amount(self, db_session):
        debit = db_session.query(func.sum(Operations.amount)).filter_by(owner_balance=self, operation_type=Operations.OperationsType.DEBIT).first()[0]
        credit = db_session.query(func.sum(Operations.amount)).filter_by(owner_balance=self, operation_type=Operations.OperationsType.CREDIT).first()[0]
        debit = 0.0 if debit is None else float(debit)
        credit = 0.0 if credit is None else float(credit)
        self.amount = credit - debit

    def check_operation(self, more_balance, db_session):
        debit = db_session.query(func.sum(Operations.amount)).filter_by(owner_balance=self, operation_type=Operations.OperationsType.CREDIT, more_balance=more_balance).first()[0]
        credit = db_session.query(func.sum(Operations.amount)).filter_by(owner_balance=more_balance, operation_type=Operations.OperationsType.DEBIT, more_balance=self).first()[0]
        return debit == credit


class Operations(DBBase):
    """Модель операций пользователя
    """
    __tablename__ = "operations"

    class OperationsType(enum.Enum):
        DEBIT = 0
        CREDIT = 1

    id = Column(Integer, primary_key=True, index=True)
    owner_balance_id = Column(Integer, ForeignKey('balances.id', ondelete='SET NULL'))
    owner_balance = relationship("Balance", backref="owner_operations", foreign_keys=[owner_balance_id])
    created = Column(DateTime(True), default=datetime.now())
    operation_type = Column(Enum(OperationsType), nullable=False, index=True, default=OperationsType.DEBIT)
    amount = Column(Numeric, nullable=False, default=0)
    more_balance_id = Column(Integer, ForeignKey('balances.id', ondelete='SET NULL'))
    more_balance = relationship("Balance", backref="more_operations", foreign_keys=[more_balance_id])
