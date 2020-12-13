from typing import List
from datetime import datetime

from fastapi import FastAPI, Depends, APIRouter, HTTPException, Query

from sqlalchemy.orm import Session

from app.connects.postgres.utils import get_db
from app.schemas import (
    BalanceSchema,
    AddBalanceSchema,
    AddBalanceResponceShema,
    TransferBalanceSchema,
    TransferBalanceResponceShema,
    OperationsListSchema
)
from app.models.balance import Balance, Operations
from app.models.auth import User
from app.utils.request import get_filters_for_list_values
from app.utils.pgsql import generate_filter, generate_order_by


router = APIRouter()

@router.get("/{balance_id}", response_model=BalanceSchema, name="balances:details")
async def get_balance_by_id(*, balance_id: int, pg: Session = Depends(get_db)):
    """Просмотр баланса"""
    db_balance = pg.query(Balance).join(User).filter(Balance.id == balance_id).first()
    if not db_balance:
        raise HTTPException(status_code=400, detail=f"Not found balance id: {balance_id}")

    return BalanceSchema(
                        id=db_balance.id,
                        username=db_balance.user.username,
                        is_active=db_balance.user.is_active,
                        amount=db_balance.amount,
                        currency=db_balance.currency.name
                    )

@router.get("/operations/{balance_id}", response_model=OperationsListSchema, name="operations:list")
async def get_segments(*,
                      balance_id: int, 
                      limit: int = Query(20),
                      offset: int = Query(0),
                      field: List[str] = Query(None),
                      value: List[str] = Query(None),
                      op: List[str] = Query(None),
                      sort_by: List[str] = Query(None),
                      sort_order: List[str] = Query(None),
                      pg: Session = Depends(get_db)
                      ):
    """Получить список операций

    Args:
        balance_id: операции по балансу
        limit: кол-во записей
        offset: начать с № записи
        field: фильтрация, указать название поля(ей - через ,)
        value: фильтрация, указать значение(я - через ,)
        op: фильтрация, указать операцию(через , ('=', '!=', '>', '<'))
        sort_by: поле по которому сортировать: ?sort_by=id (название поле)
        sort_order: направление сортировки: ?sort_order=asc (asc\desc)
        pg: конектор к postgres

    Example:
        ?offset=0&limit=10&field=more_balance_id&value=2&op=!%3D
        Сортировка списка:
            sort_by - поле по которому сортировать: ?sort_by=id (название поле)
            sort_order - направление сортировки: ?sort_order=asc (asc\desc)
        Фильтр передается:
            ?id=123 (единичное значение)
            ?id=123|456|444 (множественное значение)
    """
    db_balance = pg.query(Balance).filter(Balance.id == balance_id).first()
    if not db_balance:
        raise HTTPException(status_code=400, detail=f"Not found balance id: {balance_id}")
    filters = get_filters_for_list_values({'field': field, 'value': value, 'op': op})
    try:
        where = f"WHERE o.owner_balance_id={balance_id}"
        if len(filters) > 0:
            where_clause = []
            for w in filters:
                where_clause.append(generate_filter("o.{}".format(w['field']), w['value'], w['op']))
            where = f"{where} AND " + " AND ".join(where_clause)
        order_by = generate_order_by(sort_by, sort_order, table_pre='o')
        sql = ''' SELECT o.id, o.created, o.operation_type, o.amount, o.owner_balance_id, o.more_balance_id
                  FROM operations o {where} {order_by} LIMIT :limit OFFSET :offset'''.format(where=where,
                                                                                                  order_by=order_by
                                                                                                  )
        sql_count = ''' SELECT count(o.id) as count_r FROM public.operations o {where}'''.format(where=where)
        count_rows = pg.execute(sql_count).first()[0]
        return_data = {'items': [], 'totalCount': 0}
        if count_rows:
            db_rows = pg.execute(sql, {'limit': limit, 'offset': offset})
            return_data = {'items': [dict(row)for row in db_rows], 'totalCount': count_rows}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return return_data


@router.put("/{balance_id}", response_model=AddBalanceResponceShema, name="balances:adding")
async def adding_money(*, balance_id: int, data: AddBalanceSchema, pg: Session = Depends(get_db)):
    """Зачисление денежных средств на кошелек клиента

    Args:
        balance_id: баланс на который зачислить средства
        data: данные о кол-ве зачисляемых средств
        pg: сессия к БД postgres

    Returns:
        BalanceSchema
    """
    db_balance = pg.query(Balance).join(User).filter(Balance.id == balance_id).first()
    if not db_balance:
        raise HTTPException(status_code=400, detail=f"Not found balance id: {balance_id}")

    # patch
    if db_balance:
        pg.begin(subtransactions=True)
        try:
            system_balance = Balance.get_system_balance(pg)
            operation_from=Operations(amount=data.amount, operation_type=Operations.OperationsType.DEBIT,
                                      owner_balance=system_balance, more_balance=db_balance, created=datetime.now())
            pg.add(operation_from)
            operation_in=Operations(amount=data.amount, operation_type=Operations.OperationsType.CREDIT,
                                    owner_balance=db_balance, more_balance=system_balance, created=datetime.now())
            pg.add(operation_in)
            pg.commit()  # transaction is committed here
            # pg.flush()
            if not system_balance.check_operation(db_balance, pg) or not db_balance.check_operation(system_balance, pg):
                raise ValueError('Error when checking operations')
        except Exception as e:
            pg.rollback() # rolls back the transaction
            raise HTTPException(status_code=400, detail=str(e))
        
        system_balance.set_amount(pg)
        db_balance.set_amount(pg)
        pg.add(system_balance)
        pg.add(db_balance)
        pg.commit()

        pg.refresh(system_balance)
        pg.refresh(db_balance)
    return AddBalanceResponceShema(
            id=db_balance.id,
            username=db_balance.user.username,
            total=db_balance.amount,
            added=data.amount,
            currency=db_balance.currency.name
        )


@router.put("/transfer/{balance_id}", response_model=TransferBalanceResponceShema, name="balances:transfer")
async def transfer_money(*, balance_id: int, data: TransferBalanceSchema, pg: Session = Depends(get_db)):
    """Перевод денежных средств с одного кошелька на другой

    Args:
        balance_id: баланс c которого списываем средства
        data: данные о перечислении
        pg: сессия к БД postgres

    Returns:
        TransferBalanceSchema
    """
    db_balance = pg.query(Balance).join(User).filter(Balance.id == balance_id).first()
    if not db_balance:
        raise HTTPException(status_code=400, detail=f"Not found balance id: {balance_id}")
    if db_balance.amount < data.amount:
        raise HTTPException(status_code=400, detail=f"Insufficient funds on the balance: {balance_id}")
    db_to_balance = pg.query(Balance).filter(Balance.id == data.to_balance).first()
    if not db_to_balance:
        raise HTTPException(status_code=400, detail=f"Not found recipient's balance id: {data.to_balance}")

    # patch
    if db_balance:
        pg.begin(subtransactions=True)
        try:
            operation_from=Operations(amount=data.amount, operation_type=Operations.OperationsType.DEBIT,
                                      owner_balance=db_balance, more_balance=db_to_balance, created=datetime.now())
            pg.add(operation_from)
            operation_in=Operations(amount=data.amount, operation_type=Operations.OperationsType.CREDIT,
                                    owner_balance=db_to_balance, more_balance=db_balance, created=datetime.now())
            pg.add(operation_in)
            pg.commit()  # transaction is committed here
            # pg.flush()
            if not db_to_balance.check_operation(db_balance, pg) or not db_balance.check_operation(db_to_balance, pg):
                raise ValueError('Error when checking operations')
        except Exception as e:
            pg.rollback() # rolls back the transaction
            raise HTTPException(status_code=400, detail=str(e))
        
        db_to_balance.set_amount(pg)
        db_balance.set_amount(pg)
        pg.add(db_to_balance)
        pg.add(db_balance)
        pg.commit()

        pg.refresh(db_to_balance)
        pg.refresh(db_balance)
    return TransferBalanceResponceShema(
            id=db_balance.id,
            recipient_balance=db_to_balance.id,
            amount=data.amount,
            currency=db_balance.currency.name
        )
