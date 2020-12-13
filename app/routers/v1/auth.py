from sqlalchemy.orm import Session

from fastapi import Depends, APIRouter
from app.connects.postgres.utils import get_db
from app.schemas import (
    CreateBalanceSchema,
    BalanceSchema
)
from app.models.balance import Balance
from app.models.auth import User
from app.utils.db_utils import get_or_create


router = APIRouter()


@router.post("/", response_model=BalanceSchema, name="auth:create")
async def create_balance(*, user: CreateBalanceSchema, pg: Session = Depends(get_db)):
    """Создание клиента с кошельком

    Args:
        user: объект пользователя
        pg: сессия к БД postgres

    Returns:
        BalanceSchema
    """
    db_user, create = get_or_create(pg, User, defaults={"is_active": True}, username=user.username)
    if create:
        pg.add(db_user)

        db_balance = Balance(user=db_user)
        pg.add(db_balance)
        pg.commit()
        pg.refresh(db_user)
        pg.refresh(db_balance)
    else:
        db_balance = db_user.balance

    return BalanceSchema(
            id=db_balance.id,
            username=db_user.username,
            is_active=db_user.is_active,
            amount=db_balance.amount,
            currency=db_balance.currency.name
        )
