import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.auth import User
from app.models.balance import Balance


class TestAuthApi():
    def _setup(self, db_session):
        user = db_session.query(User).filter(User.id == 1).first()

        if not user:
            db_user = User(username='test_case',
                            is_active=True
                            )
            db_session.add(db_user)
            db_balance = Balance(user=db_user)
            db_session.add(db_balance)
            db_session.commit()
            db_session.refresh(db_user)
            db_session.refresh(db_balance)

    def _teardown(self, db_session):
        """clear db"""
        db_session.query(Balance).delete()
        db_session.query(User).delete()

    def test_create_balance(self,
                  db_session: Session,
                  client: TestClient
                  ):
        """Создание клиента с кошельком"""
        self._setup(db_session)
        url = '/v1/auth/'
        post_date = {
                    "username": "test_user_2"
                    }
        response = client.post(url, json=post_date)
        assert response.status_code == 200
        new_user = response.json()
        assert new_user['username'] == "test_user_2"
        assert new_user['amount'] == 0
        assert db_session.query(func.count(User.id)).scalar() == 2
        assert db_session.query(func.count(Balance.id)).scalar() == 2

        self._teardown(db_session)
