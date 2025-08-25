import boto3
import base64
import hashlib
import hmac
import json
import time

import requests
from enum import Enum

from exceptions import CoreException
from util.logging_util import logger
from config import NaverSmsConfig
from firebase_admin import messaging

_sns_client = None


class AWSSNSSMSType(Enum):
    Promotional = 'Promotional'
    Transactional = 'Transactional'


def _get_sns_client():
    global _sns_client
    if _sns_client is None:
        try:
            # 서울 리전 아직 지원되지 않음
            # https://docs.aws.amazon.com/ko_kr/sns/latest/dg/sns-supported-regions-countries.html
            _sns_client = boto3.client('sns', region_name='us-east-1')
        except Exception as e:
            logger.error(f'_get_sns_client:{e}')
            raise CoreException(f'_get_sns_client:{e}', 'FAILED')
    return _sns_client


def send_aws_sms_notification(phone_number: str, message: str, sms_type: AWSSNSSMSType = AWSSNSSMSType.Promotional):
    """
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html#SNS.Client.publish
    AWS SNS 를 통해서 SMS 문자메시지를 전송한다.
    :param phone_number: 핸드폰 번호 => 82-10-XXXx-XXXX or 8210XXXXXXXX 형태 둘다 가능
    :param message: 보낼 메시지 \n 로 줄바꿈 가능
    :param sms_type: 메시지 유형
        - Promotional(기본값) – 마케팅 메시지와 같이 중요하지 않은 메시지입니다.
        - Transactional – 고객 트랜잭션을 지원하는 중요한 메시지입니다(예: 멀티 팩터 인증을 위한 일회용 암호).
    """
    message_attribute = {
        'AWS.SNS.SMS.SenderID': {'DataType': 'String', 'StringValue': '52gStudio'},
        'AWS.SNS.SMS.MaxPrice': {'DataType': 'String', 'StringValue': '1.0'},
        'AWS.SNS.SMS.SMSType': {'DataType': 'String', 'StringValue': sms_type.value}
    }
    try:
        result = _get_sns_client().publish(
            PhoneNumber=phone_number,
            Message=message,
            MessageAttributes=message_attribute
        )
        logger.debug(f'Message-Id:{result}')
    except Exception as e:
        logger.error(f'_send_sms:{e}')
        raise CoreException(f'_send_sms:{e}', 'FAILED')


def send_naver_sms_notification(phone_number: str, message: str):
    """
    네이버 를 통해서 SMS 문자메시지를 전송한다.
    :param phone_number: 핸드폰 번호 => 010XXXXXXXX 형태 가능
    :param message: 보낼 메시지 \n 로 줄바꿈 가능
    """
    timestamp = str(int(time.time() * 1000))
    access_key = NaverSmsConfig.instance().ACCESS_KEY
    secret_key = NaverSmsConfig.instance().SECRET_KEY

    signature_message = 'POST' + " " + NaverSmsConfig.instance().NAVER_URI + "\n" + timestamp + "\n" + access_key
    signature_message = bytes(signature_message, 'UTF-8')
    signature = base64.b64encode(hmac.new(bytes(secret_key, 'UTF-8'), signature_message, digestmod=hashlib.sha256).digest())

    url = NaverSmsConfig.instance().NAVER_URL + NaverSmsConfig.instance().NAVER_URI

    body = {
        "type": "SMS",
        "contentType": "COMM",
        'countryCode': '82',
        "from": NaverSmsConfig.instance().FROM_PHONE_NUMBER,
        "content": message,
        "messages": [{"to": phone_number}]
    }

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": access_key,
        "x-ncp-apigw-signature-v2": signature
    }

    result = requests.post(url, data=json.dumps(body), headers=headers)
    json_result = result.json()
    if result.status_code == 202 and json_result['statusName'] == 'success':
        logger.debug(f'success_send_sms: {json_result}')
    else:
        logger.error(f'fail_send_sms:{json_result}')
        raise CoreException(f'fail_send_sms:{json_result}', 'FAILED')


def send_push_to_topic(topic: str, title: str, body) -> str:
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        topic=topic,
    )
    response = messaging.send(message)
    print(f'response : {response}')
    return response


def subscribe_to_topic(token: str, topic: str):
    print(f'topic : {topic}')
    print(f'token : {token}')

    response = messaging.subscribe_to_topic([token], topic)
    print(f'response : {response}')
    return response


def unsubscribe_from_topic(token: str, topic: str):
    response = messaging.unsubscribe_from_topic([token], topic)
    return response


if __name__ == '__main__':
    import logging

    logger.set_default_logger_level(__name__, logging.DEBUG)

    # 테스트를 위해서는 개인 휴대폰 번호를 입력해서 테스트하자.(꼭 바꿔주세요.)
    # aws는 국가코드 필요
    send_aws_sms_notification('82103284XXXX', '안녕하세요. 고객님\n52g Studio 입니다.\nAWS 테스트 문자 전송 합니다.',
                              sms_type=AWSSNSSMSType.Transactional)

    # 네이버는 한국 대상이므로 반드시 국가코드 제거 필요
    send_naver_sms_notification('0103284XXXX', '안녕하세요. 고객님\n52g Studio 입니다.\n네이버 테스트 문자 전송 합니다.')
