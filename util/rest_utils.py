import requests
from flask import json

from exceptions import CoreException


def call_rest_api(http_method, url, jwt_token=None, request_entity=None, headers=None,
                  conn_timeout=5.0, read_timeout=5.0):
    """
    지정된 HTTP API를 호출한다.
    :param http_method: HTTP 메소드 (GET, POST, PUT, DELETE, PATCH)
    :param url: API의 URL
    :param jwt_token: Bearer 토큰으로 사용할 JWT
    :param request_entity: query나 payload에 해당하는 key-value 쌍
    :param headers: HTTP 헤더
    :param conn_timeout: 연결 타임아웃 기본값 5초 None 일 경우 무한
    :param read_timeout: 응답 타임아웃 기본값 5초 None 일 경우 무한
    :return:
    """
    default_headers = {'Content-Type': 'application/json; charset=utf-8'}
    if jwt_token:
        default_headers['Authorization'] = f'Bearer {jwt_token}'

    timeouts = (conn_timeout, read_timeout)

    try:
        if headers:
            default_headers.update(headers)

        if http_method == 'GET':
            response = requests.get(url, headers=default_headers, params=request_entity, timeout=timeouts)
        else:
            data = None
            if request_entity:
                data = json.dumps(request_entity)

            if http_method == 'POST':
                response = requests.post(url, headers=default_headers, data=data, timeout=timeouts)
            elif http_method == 'PUT':
                response = requests.put(url, headers=default_headers, data=data, timeout=timeouts)
            elif http_method == 'DELETE':
                response = requests.delete(url, headers=default_headers, data=data, timeout=timeouts)
            elif http_method == 'PATCH':
                response = requests.patch(url, headers=default_headers, data=data, timeout=timeouts)
            else:
                raise CoreException(f'call_rest_api: {http_method}', 'REST_CALL_ERROR')

        response.raise_for_status()
    except Exception as e:
        raise CoreException(f'call_rest_api({http_method}):{e}', 'REST_CALL_ERROR')

    return response
