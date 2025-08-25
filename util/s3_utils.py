import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from util.logging_util import logger
from contants import S3_BUCKET_NAME_FORMAT, DEFAULT_REGION

from enum import Enum, auto

cache_client = None
cache_resource = None


def _find_client_from_cache(region):
    global cache_client
    if cache_client is None:
        cache_client = {}

    if cache_client.get(region):
        s3_client = cache_client[region]
        if s3_client is None:
            s3_client = boto3.client('s3', config=Config(signature_version='s3v4'), region_name=region)
            cache_client[region] = s3_client
    else:
        s3_client = boto3.client('s3', config=Config(signature_version='s3v4'), region_name=region)
        cache_client[region] = s3_client

    return s3_client


def _find_resource_from_cache(region):
    global cache_resource
    if cache_resource is None:
        cache_resource = {}

    if cache_resource.get(region):
        s3_resource = cache_resource[region]
        if s3_resource is None:
            s3_resource = boto3.resource('s3', config=Config(signature_version='s3v4'), region_name=region)
            cache_resource[region] = s3_resource
    else:
        s3_resource = boto3.resource('s3', config=Config(signature_version='s3v4'), region_name=region)
        cache_resource[region] = s3_resource

    return s3_resource


def get_bucket_name(region=DEFAULT_REGION):
    """
    constants.py 파일에 지정된 포맷으로 버킷명을 얻는다.
    :param region: 버킷명에 포함될 리전명
    :return:
    """
    return S3_BUCKET_NAME_FORMAT.format(region=region)


def get_s3_base_url(region=DEFAULT_REGION):
    """
    S3 의 기본 URL 을 반환한다.
    :param region: URL 포함될 리전명
    """
    return f'https://{get_bucket_name()}.s3.{region}.amazonaws.com'


def put_object_contents(source_contents, object_key, region=DEFAULT_REGION, bucket_name=get_bucket_name()):
    """
    소스 파일을 지정한 키로 지정된 버킷에 저장한다.
    :param region: 버킷의 리전
    :param bucket_name: 버킷명
    :param source_contents: 소스 파일 binary
    :param object_key: 객체키
    :return:
    """
    logger.debug(
        f'region:{region}, bucket_name:{bucket_name}, source_key:{source_contents}, destination_key:{object_key}')
    try:
        s3_client = _find_client_from_cache(region)
        s3_client.put_object(Bucket=bucket_name, Body=source_contents, Key=object_key)
    except Exception as e:
        logger.error(f'put_object_contents: {e}')
        raise e


def delete_object(object_key, region=DEFAULT_REGION, bucket_name=get_bucket_name()):
    """
    버킷에 있는 객체를 삭제한다.
    :param region: 버킷의 리전
    :param bucket_name: 버킷명
    :param object_key: 삭제할 객체명
    :return:
    """
    logger.debug(
        f'region:{region}, bucket_name:{bucket_name}, object_key:{object_key}')
    try:
        s3_client = _find_client_from_cache(region)
        response = s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        return response
    except Exception as e:
        logger.error(f'delete_object: {e}')
        raise e


def delete_objects(object_key_list, region=DEFAULT_REGION, bucket_name=get_bucket_name()):
    """
    버킷에 있는 객체들을 삭제한다.
    :param region: 버킷의 리전
    :param bucket_name: 버킷명
    :param object_key_list: 삭제할 객체 키 목록
    :return:
    """
    try:
        s3_client = _find_client_from_cache(region)
        response = None
        if len(object_key_list) > 0:
            delete_keys = []
            for object_key in object_key_list:
                logger.debug(f'object_key:{object_key}')
                delete_keys.append({'Key': object_key})
            delete_dict = {'Objects': delete_keys, 'Quiet': False, }
            response = s3_client.delete_objects(Bucket=bucket_name, Delete=delete_dict)
        return response
    except Exception as e:
        logger.error(f'delete_objects: {e}')
        raise e


def delete_all_objects_with_prefix(prefix, region=DEFAULT_REGION, bucket_name=get_bucket_name()):
    """
    버킷에서 해당 접두어를 가진 객체를 삭제한다.
    :param region: 버킷의 리전
    :param bucket_name: 버킷명
    :param prefix: 삭제할 객체의 접두어
    :return:
    """
    try:
        s3_resource = _find_resource_from_cache(region)
        bucket = s3_resource.Bucket(bucket_name)
        bucket.objects.filter(Prefix=prefix).delete()

    except Exception as e:
        logger.error(f'delete_all_objects_with_prefix: {e}')
        raise e


def copy_all_object_same_region(source_prefix, destination_prefix,
                                region=DEFAULT_REGION, bucket_name=get_bucket_name()):
    """
    버킷에서 해당 접두어를 가진 객체를 다른 접두를 가진 객체로 복사한다(덮어쓰기도 가능).
    :param region: 버킷의 리전
    :param bucket_name: 버킷명
    :param source_prefix: 복사할 소스 키의 프리픽스
    :param destination_prefix: 복사될 타겟 키의 프리픽스
    :return:
    """
    logger.debug(
        f'region_name:{region} bucket_name:{bucket_name} source_prefix:{source_prefix} '
        f'destination_prefix:{destination_prefix}')
    try:
        s3_client = _find_client_from_cache(region)

        response = s3_client.list_objects(Bucket=bucket_name, Prefix=source_prefix)
        for content in response['Contents']:
            source_key = content['Key']
            destination_key = source_key.replace(source_prefix, destination_prefix)
            logger.debug(f's_key:{source_key}, d_key:{destination_key}')
            # MetadataDirective='REPLACE' => 존재하던 객체를 다시 덮어써도 오류(This copy request is illegal) 발생하지 않음
            s3_client.copy_object(CopySource=f'{bucket_name}/{source_key}',
                                  Bucket=bucket_name, Key=destination_key,
                                  MetadataDirective='REPLACE')

    except Exception as e:
        logger.error(f'copy_all_object_same_region: {e}')
        raise e


def copy_object_same_region(source_key, destination_key, region=DEFAULT_REGION, bucket_name=get_bucket_name()):
    """
    버킷에 있는 객체를 다른 객체로 복사한다(덮어쓰기도 가능).
    :param region: 버킷의 리전
    :param bucket_name: 버킷명
    :param source_key: 복사할 객체키
    :param destination_key: 복사되는 객체키
    :return:
    """
    logger.debug(
        f'region_name:{region} bucket_name:{bucket_name} source_key:{source_key} destination_key:{destination_key}')
    try:
        s3_client = _find_client_from_cache(region)

        # MetadataDirective='REPLACE' => 존재하던 객체를 다시 덮어써도 오류(This copy request is illegal) 발생하지 않음
        s3_client.copy_object(CopySource=f'{bucket_name}/{source_key}',
                              Bucket=bucket_name, Key=destination_key,
                              MetadataDirective='REPLACE')

    except Exception as e:
        logger.error(f'copy_object_same_region: {e}')
        raise e


def move_object_same_region(source_key, destination_key, region=DEFAULT_REGION, bucket_name=get_bucket_name()):
    """
    버킷에 있는 객체를 다른 객체로 이동한다(복사하고 소스 객체를 삭제).
    :param region: 버킷의 리전
    :param bucket_name: 버킷명
    :param source_key: 복사할 객체키
    :param destination_key: 복사되는 객체키
    :return:
    """
    copy_object_same_region(source_key, destination_key, region=region, bucket_name=bucket_name)
    delete_object(source_key, region=region, bucket_name=bucket_name)


class S3PreSignedURLOpType(Enum):
    GET = auto()
    PUT = auto()


def create_presigned_url(object_key: str, url_type: S3PreSignedURLOpType = S3PreSignedURLOpType.GET,
                         expiration: int = 3600, region: str = DEFAULT_REGION,
                         bucket_name: str = get_bucket_name()) -> str:
    """
    버킷에 있는 객체를 공유하기 위한 서명된 URL을 생성한다.
    :param region: 버킷의 리전
    :param url_type: Pre Signed URL 생성시 줄수 있는 권한 GET, PUT
    :param bucket_name: 버킷명
    :param object_key: 서명된 URL 대상 객체 키
    :param expiration: 서명된 URL의 만료 시간
    :return: 문자열인 서명된 URL. 오류가 발생하면 None을 리턴.
    """

    # Generate a presigned URL for the S3 object
    # s3_client = boto3.client('s3', verify=False)
    s3_client = _find_client_from_cache(region)
    try:
        presigned_url = s3_client.generate_presigned_url(f'{url_type.name.lower()}_object',
                                                         Params={'Bucket': bucket_name,
                                                                 'Key': object_key},
                                                         ExpiresIn=expiration,
                                                         HttpMethod=url_type.name)
    except ClientError as e:
        logger.error(e)
        return ''

    # The response contains the presigned URL
    return presigned_url


if __name__ == '__main__':
    # 기본 버킷명
    print(get_bucket_name())

    # 접두어
    local_prefix = 's3'
    local_destination_prefix = 'new_s3'

    # 키명
    local_object_key1 = f'{local_prefix}_util'
    local_object_key2 = f'{local_prefix}_util2'
    local_object_key3 = f'{local_prefix}_util3'

    # s3 업로드
    with open('./s3_utils.py', 'r') as file:
        binary = file.read()
        put_object_contents(binary, local_object_key1)
        put_object_contents(binary, local_object_key2)

    # s3 키로 복사
    copy_object_same_region(local_object_key1, local_object_key3)

    # s3 source source prefix - destination prefix 접두어 로 복사
    copy_all_object_same_region(local_prefix, local_destination_prefix)

    # s3 임시 다운로드 url
    print(create_presigned_url(local_object_key1))

    # s3에서 삭제 키명으로
    delete_object(local_object_key1)

    # s3에서 삭제 접두어로
    delete_all_objects_with_prefix(local_prefix)
    delete_all_objects_with_prefix(local_destination_prefix)
