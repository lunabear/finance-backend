from pynamodb.transactions import TransactWrite
from pynamodb.connection import Connection
from pynamodb.models import Model as DDBModel
from contants import DEFAULT_REGION


def save_with_transaction(models: [DDBModel], region: str = DEFAULT_REGION):
    """
    다이나모 DB 의 트랙잭션 처리를 하여 신규 객체를 생성한다.
    :param models: 트랜잭션 처리를 원하는 DDBModel 객체 리스트
    :param region: AWS 리전
    :return:
    """
    connection = Connection(region=region)
    with TransactWrite(connection=connection) as transaction:
        for model in models:
            transaction.save(model)


def delete_with_transaction(models: [DDBModel], region: str = DEFAULT_REGION):
    """
    다이나모 DB 의 트랙잭션 처리를 하여 객체 목록을 삭제한다.
    :param models: 트랜잭션 처리를 원하는 DDBModel 객체 리스트
    :param region: AWS 리전
    :return:
    """
    connection = Connection(region=region)
    with TransactWrite(connection=connection) as transaction:
        for model in models:
            transaction.delete(model)
