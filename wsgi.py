import traceback
from http import HTTPStatus

from api import create_app
from util.logging_util import logger

app = create_app()


@app.errorhandler(Exception)
def handle_root_exception(error):
    logger.error(f'flask errorhandler occurred:{traceback.print_exc()}')
    try:
        message = error.message
    except AttributeError:
        message = str(error)

    try:
        code = error.code
        if 100 > code or code >= 600:
            code = HTTPStatus.INTERNAL_SERVER_ERROR
    except AttributeError:
        code = HTTPStatus.INTERNAL_SERVER_ERROR
    except TypeError:
        code = HTTPStatus.INTERNAL_SERVER_ERROR

    try:
        error_code = error.error_code
    except AttributeError as e:
        logger.warning(f'No error_code in AttributeError:{e}')
        if 400 <= code < 500:
            error_code = 'Flask request error'
        else:
            error_code = 'Flask internal error'

    logger.error(f'message:{message}, errorCode:{error_code}, error:{error}, code:{code}')
    return {'message': message, 'errorCode': error_code, 'error': error.__class__.__name__}, code


if __name__ == '__main__':
    # 금융 백엔드 로컬 서버 실행
    # 로컬 실행시 모듈이 2번 로딩되면 use_reloader=False 설정하면 됨.
    app.run(host='0.0.0.0', debug=True, port=8080)
