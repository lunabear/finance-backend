import datetime
from functools import wraps

from flask_jwt_extended import get_jwt, create_access_token, verify_jwt_in_request

from contants import UserScopeType
from exceptions import AccessDeniedException
from util.logging_util import logger


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        scope = get_jwt().get('scope')
        if scope not in (UserScopeType.ADMIN.name, UserScopeType.TEST.name):
            raise AccessDeniedException('Only allowed to Admins!', 'JWT_ERROR')
        else:
            return func(*args, **kwargs)

    return wrapper


def user_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        scope = get_jwt().get('scope')
        if scope not in (UserScopeType.ADMIN.name, UserScopeType.USER.name, UserScopeType.TEST.name):
            raise AccessDeniedException('Only allowed to USER!', 'JWT_ERROR')
        else:
            return func(*args, **kwargs)

    return wrapper


def otp_user_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        scope = get_jwt().get('scope')
        if scope not in (UserScopeType.OTP.name):
            raise AccessDeniedException('Only allowed to OTP User!', 'JWT_ERROR')
        else:
            return func(*args, **kwargs)

    return wrapper


def jwt_optional(func):
    """
    jwt_required(optional=True) 을 wrapping 한 데코레이터
    jwt 유무에 따른 분기가 필요한 Rest API 에서 사용한다.
    @jwt_required(optional=True) 와 동일하며 추가적인 로직이 필요한 경우 아래처럼 구현한다.
    이 예제 에서는 jwt 여부에 따른 추가적인 로깅 작업을 한다.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if verify_jwt_in_request(optional=True):
            scope = get_jwt().get('scope')
            logger.debug(f'jwt is exist. scope : {scope}')
        else:
            logger.debug('jwt is not exist')
        return func(*args, **kwargs)

    return wrapper


def generate_token(username: str, scope: str, expires_delta: int = 86400) -> str:
    """
    해당 사용장의 정보(이름, 아이디, 이메일, 핸드폰 번호 등등 프로젝트에 맞게)와 scope(권한) 를 이용하여 JWT 토큰을 생성한다.
    :param username: 사용자를 구분할수 있는 정보(프로젝트에 맞게 아이디, 전화번호, 이메일 등 어떠것도 될수 있다.)
    :param scope: 일종의 권한(템플릿 예제는 user, admin 으로 구분한다.)
    :param expires_delta: jwt token 이 만료되는 시간 기본값은 1일
                        (None 으로 줄 경우 JWT_ACCESS_TOKEN_EXPIRES 설정을 따라간다. False 일 경우 무제한)
    :return:
    """
    identity_data = username
    user_data = {'username': username, 'scope': scope}

    if expires_delta:
        expires_delta = datetime.timedelta(seconds=expires_delta)
        access_token = create_access_token(identity=identity_data,
                                           additional_claims=user_data,
                                           expires_delta=expires_delta)
    else:
        access_token = create_access_token(identity=identity_data,
                                           additional_claims=user_data)
    return access_token
