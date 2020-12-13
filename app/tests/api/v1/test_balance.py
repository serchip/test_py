import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.auth import User
from app.models.balance import Balance
from app.tests.api.test_case import TestCase


class TestBalanceApi(TestCase):
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

    def add_money(self,
                db_session: Session,
                client: TestClient,
                balance_id: int
                ):
        """Пополнение баланса"""
        url = '/v1/balances/{}'.format(balance_id)
        post_date = {'amount': 22}
        response = client.put(url, json=post_date)
        assert response.status_code == 200
        data_detail=response.json()
        return data_detail

    def test_adding_money(self,
                  db_session: Session,
                  client: TestClient
                  ):
        """Зачисление денежных средств на кошелек клиента"""
        self._setup(db_session)

        db_balance = db_session.query(Balance).join(User).first()
        data_detail = self.add_money(db_session, client, db_balance.id)
        assert data_detail['id'] == db_balance.id
        assert data_detail['username'] == db_balance.user.username
        assert data_detail['total'] == 22
        assert data_detail['added'] ==  22
        assert data_detail['currency'] ==  "USD"
        db_system_balance = db_session.query(Balance).join(User).filter(User.username=='system_user').first()
        assert db_system_balance.amount == -22

        db_balance = db_session.query(Balance).join(User).first()
        url = f"/v1/balances/{db_balance.id}"
        post_date = {'amount': 10}
        response = client.put(url, json=post_date)
        assert response.status_code == 200
        data_detail=response.json()
        assert data_detail['id'] == db_balance.id
        assert data_detail['username'] == db_balance.user.username
        assert data_detail['total'] == 32
        assert data_detail['added'] ==  10
        assert data_detail['currency'] ==  "USD"

        db_system_balance = db_session.query(Balance).join(User).filter(User.username=='system_user').first()
        assert db_system_balance.amount == -32

        self._teardown(db_session)

    def test_adding_money_faild_balance(self,
                  db_session: Session,
                  client: TestClient
                  ):
        """Зачисление денежных средств на не существующий кошелек клиента"""
        url = f"/v1/balances/2323"
        post_date = {'amount': 22}
        response = client.put(url, json=post_date)
        assert response.status_code == 400
        assert response.json()['detail'] == f"Not found balance id: 2323"

    def test_transfer_money(self,
                    db_session: Session,
                    client: TestClient
                  ):
        """Перевод денежных средств с одного кошелька на другой"""
        self._setup(db_session)
        db_balance = db_session.query(Balance).first()
        data_detail = self.add_money(db_session, client, db_balance.id)

        db_balance = db_session.query(Balance).first()
        assert db_balance.amount == 22

        db_recipient_user = User(username='recipient_user',
                        is_active=True
                        )
        db_session.add(db_recipient_user)
        db_recipient_balance = Balance(user=db_recipient_user)
        db_session.add(db_recipient_balance)
        db_session.commit()
        db_session.refresh(db_recipient_user)
        db_session.refresh(db_recipient_balance)

        url = f"/v1/balances/transfer/{db_balance.id}"
        post_date = {'amount': 10, 'to_balance': db_recipient_balance.id}
        response = client.put(url, json=post_date)
        assert response.status_code == 200
        data_detail=response.json()
        assert data_detail['id'] == db_balance.id
        assert data_detail['recipient_balance'] == db_recipient_balance.id
        assert data_detail['amount'] == 10
        assert data_detail['currency'] ==  "USD"

        db_recipient_balance = db_session.query(Balance).filter(Balance.id==db_recipient_balance.id).first()
        assert db_recipient_balance.amount == 10

        db_balance = db_session.query(Balance).filter(Balance.id==db_balance.id).first()
        assert db_balance.amount == 12

        self._teardown(db_session)

    def test_transfer_money_not_found_from_user(self,
                    db_session: Session,
                    client: TestClient
                  ):
        """Перевод денежных средств с несуществующего кошелька"""
        self._setup(db_session)
        db_balance = db_session.query(Balance).first()
        data_detail = self.add_money(db_session, client, db_balance.id)

        db_balance = db_session.query(Balance).first()
        assert db_balance.amount == 22

        url = f"/v1/balances/transfer/1221"
        post_date = {'amount': 10, 'to_balance': db_balance.id}
        response = client.put(url, json=post_date)
        assert response.status_code == 400
        assert response.json()['detail'] == f"Not found balance id: 1221"

        self._teardown(db_session)

    def test_transfer_money_not_found_recipient_balance(self,
                    db_session: Session,
                    client: TestClient
                  ):
        """Перевод денежных средств на несуществующий кошелька"""
        self._setup(db_session)
        db_balance = db_session.query(Balance).first()
        data_detail = self.add_money(db_session, client, db_balance.id)

        db_balance = db_session.query(Balance).first()
        assert db_balance.amount == 22

        url = f"/v1/balances/transfer/{db_balance.id}"
        post_date = {'amount': 10, 'to_balance': 121212}
        response = client.put(url, json=post_date)
        assert response.status_code == 400
        assert response.json()['detail'] == f"Not found recipient's balance id: 121212"

        self._teardown(db_session)

    def test_transfer_money_zero_balance(self,
                    db_session: Session,
                    client: TestClient
                  ):
        """Перевод денежных средств, недостаточно стредст у пользователя"""
        self._setup(db_session)
        db_balance = db_session.query(Balance).first()
        data_detail = self.add_money(db_session, client, db_balance.id)

        db_balance = db_session.query(Balance).first()
        assert db_balance.amount == 22
        db_recipient_user = User(username='recipient_user',
                        is_active=True
                        )
        db_session.add(db_recipient_user)
        db_recipient_balance = Balance(user=db_recipient_user)
        db_session.add(db_recipient_balance)
        db_session.commit()
        db_session.refresh(db_recipient_user)
        db_session.refresh(db_recipient_balance)

        url = f"/v1/balances/transfer/{db_balance.id}"
        post_date = {'amount': 100, 'to_balance': db_recipient_balance.id}
        response = client.put(url, json=post_date)
        assert response.status_code == 400
        assert response.json()['detail'] == f"Insufficient funds on the balance: {db_balance.id}"

        self._teardown(db_session)


    def test_detail(self,
                  db_session: Session,
                  client: TestClient
                  ):
        """Просмотр баланса пользователя"""
        self._setup(db_session)
        #-- detail --
        db_balance = db_session.query(Balance).join(User).first()

        url = '/v1/balances/{}'.format(db_balance.id)
        response = client.get(url)
        assert response.status_code == 200
        date_detail=response.json()
        assert date_detail['id'] == db_balance.id
        assert date_detail['username'] == db_balance.user.username
        assert date_detail['is_active'] == db_balance.user.is_active
        assert date_detail['amount'] == db_balance.amount
        assert date_detail['currency'] ==  "USD"

        self._teardown(db_session)

    def test_detail_not_exist_balance(self,
                  db_session: Session,
                  client: TestClient
                  ):
        """Просмотр не существующего баланса"""
        self._setup(db_session)
        #-- detail --
        db_balance = db_session.query(Balance).join(User).first()

        url = '/v1/balances/12212'
        response = client.get(url)
        assert response.status_code == 400
        assert response.json()['detail'] == f"Not found balance id: 12212"

        self._teardown(db_session)


    def test_operations_list(self,
                  db_session: Session,
                  client: TestClient
                  ):
        """список операций по балансу"""
        self._setup(db_session)
        balance1 = db_session.query(Balance).first()
        data_detail = self.add_money(db_session, client, balance1.id)
        db_system_balance = db_session.query(Balance).join(User).filter(User.username=='system_user').first()

        balance1 = db_session.query(Balance).first()
        assert balance1.amount == 22

        user2 = User(username='user2',
                        is_active=True
                        )
        db_session.add(user2)
        balance2 = Balance(user=user2)
        db_session.add(balance2)
        db_session.commit()
        db_session.refresh(user2)
        db_session.refresh(balance2)

        url = f"/v1/balances/transfer/{balance1.id}"
        post_date = {'amount': 10, 'to_balance': balance2.id}
        response = client.put(url, json=post_date)
        assert response.status_code == 200

        url = f"/v1/balances/operations/{balance1.id}"
        response = client.get(url)
        print(response.json())
        assert response.status_code == 200
        data_list = response.json()
        assert data_list['totalCount'] == 2
        assert db_system_balance.id in [o['more_balance_id'] for o in data_list['items']]
        assert balance2.id in [o['more_balance_id'] for o in data_list['items']]

        response = client.get(f'{url}?limit=1')
        assert response.status_code == 200
        data_list = response.json()
        assert len(data_list['items']) == 1
        assert data_list['totalCount'] == 2

        response = client.get(f'{url}?limit=10&offset=1')
        assert response.status_code == 200
        data_list = response.json()
        assert len(data_list['items']) == 1
        assert data_list['totalCount'] == 2

        response = client.get(f'{url}?field=more_balance_id&value={db_system_balance.id}&op=!%3D')
        assert response.status_code == 200
        data_list = response.json()
        assert len(data_list['items']) == 1
        assert data_list['totalCount'] == 1
        assert balance2.id in [o['more_balance_id'] for o in data_list['items']]


        response = client.get(f'{url}?sort_by=id&sort_order=asc')
        assert response.status_code == 200
        data_list = response.json()
        assert [2, 3] == [o['id'] for o in data_list['items']]
        response = client.get(f'{url}?sort_by=id&sort_order=desc')
        assert response.status_code == 200
        data_list = response.json()
        assert [3, 2] == [o['id'] for o in data_list['items']]

        self._teardown(db_session)
