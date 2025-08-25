from enum import Enum, auto
import boto3


# JWT User Scope
class UserScopeType(Enum):
    USER = auto()
    ADMIN = auto()
    OTP = auto()
    TEST = auto()


# AWS Region
DEFAULT_REGION = 'ap-northeast-2'

# AWS S3 : 금융 백엔드 서비스용 스토리지  
S3_BUCKET_NAME_FORMAT = 'dev-{region}-finance-backend-storage'


def get_config_from_param_store(param_name: str, with_description: bool = True) -> str:
    """
    AWS Parameter Store 에서 해당 파라미터 이름의 값을 얻어온다.
    """
    print(f'loading... get_config_from_param_store : {param_name}')
    region = boto3.session.Session().region_name
    ssm = boto3.client('ssm', region)
    parameter = ssm.get_parameter(
        Name=param_name, WithDecryption=with_description
    )

    return parameter['Parameter']['Value']


class SingletonInstance:
    """
    싱글톤이 필요한 클래스 생성시 이 클래스를 상속받아서 사용한다.
    config 모듈 참조
    """
    __instance = None

    @classmethod
    def __get_instance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instance = cls.__get_instance
        return cls.__instance

