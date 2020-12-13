

class TestCase:
    def _auth_token(self, client):
        response = client.post(url='/token', data={"username": "test_case", "password": "test_passwd"})
        auth_res = response.json()
        assert response.status_code == 200
        assert 'access_token' in auth_res.keys()
        return auth_res['access_token']

class TestCREDLCasesMixin:
    # TODO 
    pass