from datetime import datetime
from typing import Optional, List, Dict, Union
from enum import Enum, IntEnum
from pydantic import BaseModel, Field, condecimal


class BalanceSchema(BaseModel):
    """
    Model for balance
    """
    id: int
    username: str
    is_active: bool
    amount: condecimal(max_digits=12, decimal_places=2)
    currency: str

class AddBalanceSchema(BaseModel):
    """
    Model for adding balance
    """
    amount: float

class AddBalanceResponceShema(BaseModel):
    """
    Responce for adding balance
    """
    id: int
    username: str
    total: condecimal(max_digits=12, decimal_places=2)
    added: condecimal(max_digits=12, decimal_places=2)
    currency: str


class TransferBalanceSchema(BaseModel):
    """
    Model for money transfer
    """
    to_balance: int
    amount: float

class TransferBalanceResponceShema(BaseModel):
    """
    Responce for money transfer
    """
    id: int
    recipient_balance: int
    amount: condecimal(max_digits=12, decimal_places=2)
    currency: str

class OperationsTypeType(str, Enum):
    """типы операций """
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"

class OperationShema(BaseModel):
    """Схема для одной операции"""
    id: int
    created: datetime
    operation_type: OperationsTypeType
    amount: condecimal(max_digits=12, decimal_places=2)
    owner_balance_id: int
    more_balance_id: int

class OperationsListSchema(BaseModel):
    """Схема ответа список операций пльзователя"""
    items: List[OperationShema] = None
    totalCount: int = 0
