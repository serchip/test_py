"""
request.py
====================================
Вспомагательные функции для работы с request параметрами
"""
import requests
from typing import Any
from datetime import datetime
from operator import itemgetter

DEFAULT_LIMIT = 10
DEFAULT_OFFSET = 0

def get_limit_offset(args: dict) -> (int, int):
    """
        Получить значение limit и offset из QueryParams
    :param args: query параметры
    :return: список со значениями limit, offset
    """
    limit = args.get('limit', None)
    if not limit:
        limit = DEFAULT_LIMIT
    else:
        limit = int(limit[0])

    offset = args.get('offset', None)
    if not offset:
        offset = DEFAULT_OFFSET
    else:
        offset = int(offset[0])

    return limit, offset


def get_filters_for_list_view(args: dict) -> dict:
    filters = {}
    for key, value in args.items():
        if ',' in value[0]:
            _values = value[0].split(',')
            _value = '|'.join(item.upper() for item in _values)
            filters[key] = _value
        else:
            filters[key] = value[0].upper()
    return filters


def get_filters_for_list_values(args: dict) -> list:
    """
        Получить значение limit и offset из QueryParams
    Args:
        args: query параметры
    :return: filters в виде листа
    """
    filters = []
    field = args.get('field', None)
    if field:
        value = args.get('value')
        op = args.get('op')
        for i, name in enumerate(field):
            filters.append({'field': name, 'value': value[i], 'op': op[i]})
    return filters

def get_on_request(field: Any, default_value: Any) -> Any:
    """
    Функция получения значений
    Args:
        field: поле
        default_value: если пустое то подставим это значение
    Return:
        значение поля или дефолтное
    """
    if isinstance(field, datetime):
        if field.timestamp() < 10:
            return default_value
    if field:
        return field
    return default_value


def safe_list_get (l: list, idx: int=0, default: Any = None) -> Any:
    """
    Функция получения значений
    Args:
        l: список
        idx: индекс
        default: дефолтное значение
    Return:
        значение поля или дефолтное
    """
    try:
        return l[idx]
    except IndexError:
        return default

# ====== requests

class ClientAPIException(Exception):

    def __init__(self, response):
        self.code = 0
        try:
            json_res = response.json()
        except ValueError:
            self.message = 'Invalid JSON error message: {}'.format(response.text)
        else:
            self.code = json_res['code']
            self.message = json_res['msg']
        self.status_code = response.status_code
        self.response = response
        self.request = getattr(response, 'request', None)

    def __str__(self):  # pragma: no cover
        return 'APIError(code=%s): %s' % (self.code, self.message)


class ClientRequestException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'ClientRequestException: %s' % self.message


class ClientApi:
    """скелет по загрузке данных"""
    API_KEY: str
    API_SECRET: str
    API_URL: str

    def __init__(self, api_key: str = None, api_secret: str = None, requests_params: dict = [], headers: dict = None):
        """
        API Client constructor
        :param api_key: ключ
        :param api_secret: секретный ключ
        :param requests_params: параметры по умолчаню
        """
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self._requests_params = requests_params
        self.session = self._init_session(headers=headers)
        self.response = None

    def _create_api_uri(self, path: str):
        """создать полный урл к api"""
        return self.API_URL + path

    def _init_session(self, headers: dict = None):
        """
        Инициализируем сессию для запроса
        :param headers: заголовки, если они нужны
        :return: request.session
        """
        session = requests.session()
        if headers:
            session.headers.update(headers)
        return session

    def _request(self, method: str, uri: str, force_params: bool = False, **kwargs):
        """

        :param method: метод
        :param uri: полный url к api
        :param force_params: передать параметры через url
        :param kwargs: доп параметры
        :return: Response
        """
        # default requests timeout
        kwargs['timeout'] = 10

        kwargs['data'].update({'api_key': self.API_KEY, 'api_secret': self.API_SECRET})
        # add our global requests params
        if self._requests_params:
            kwargs.update(self._requests_params)
        data = kwargs.get('data', None)
        if data and isinstance(data, dict):
            kwargs['data'] = data

            # find any requests params passed and apply them
            if 'requests_params' in kwargs['data']:
                # merge requests params into kwargs
                kwargs.update(kwargs['data']['requests_params'])
                del (kwargs['data']['requests_params'])

        if data:
            # Remove any arguments with values of None.
            kwargs['data'] = self._order_params(kwargs['data'])
            null_args = [i for i, (key, value) in enumerate(kwargs['data']) if value is None]
            for i in reversed(null_args):
                del kwargs['data'][i]

        # if get request assign data array to params value for requests lib
        if data and (method == 'get' or force_params):
            kwargs['params'] = '&'.join('%s=%s' % (data[0], data[1]) for data in kwargs['data'])
            del (kwargs['data'])

        self.response = getattr(self.session, method)(uri, **kwargs)
        return self._handle_response()

    def _order_params(self, data):
        """отсортировать для удаления None"""
        params = []
        for key, value in data.items():
            params.append((key, value))
        # sort parameters by key
        params.sort(key=itemgetter(0))
        return params

    def _request_api(self, method: str, path: str, **kwargs):
        """основной метод запроса данных"""
        uri = self._create_api_uri(path)

        return self._request(method, uri, **kwargs)


    def _handle_response(self):
        """Преобразуем ответ в удобный формат"""
        if not str(self.response.status_code).startswith('2'):
            raise ClientAPIException(self.response)
        try:
            return self.response.json()
        except ValueError:
            raise ClientRequestException('Invalid Response: %s' % self.response.text)

    def get(self, path, **kwargs):
        return self._request_api('get', path, **kwargs)

