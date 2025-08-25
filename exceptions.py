from http import HTTPStatus


class ApiBaseException(Exception):
    def __init__(self, message=None, error_code=None, code=None):
        Exception.__init__(self)
        if message:
            self.message = message
        else:
            if code:
                self.message = code.description

        self.error_code = error_code
        self.code = code
        self.error = self.__class__.__name__

    def get_error_message(self):
        return self.message, self.error_code, self.error, self.code

    def __str__(self):
        return '<%s %s %s %s>' % (self.message, self.error_code, self.error, self.code)


class CoreException(ApiBaseException):
    def __init__(self, message, error_code):
        super().__init__(message, error_code, HTTPStatus.INTERNAL_SERVER_ERROR)


class BadRequestException(ApiBaseException):
    def __init__(self, message, error_code):
        super().__init__(message, error_code, HTTPStatus.BAD_REQUEST)


class EntityNotFoundException(ApiBaseException):
    def __init__(self, message, error_code):
        super().__init__(message, error_code, HTTPStatus.UNPROCESSABLE_ENTITY)


class AccessDeniedException(ApiBaseException):
    def __init__(self, message, error_code):
        super().__init__(message, error_code, HTTPStatus.FORBIDDEN)


class UnauthorizedException(ApiBaseException):
    def __init__(self, message, error_code):
        super().__init__(message, error_code, HTTPStatus.UNAUTHORIZED)


class UserAlreadyExistException(ApiBaseException):
    def __init__(self, message, error_code):
        super().__init__(message, error_code, HTTPStatus.CONFLICT)


class AlreadyExistsException(ApiBaseException):
    def __init__(self, message, error_code):
        super().__init__(message, error_code, HTTPStatus.CONFLICT)


class DuplicateKeyException(ApiBaseException):
    def __init__(self, message, error_code):
        super().__init__(message, error_code, HTTPStatus.CONFLICT)


class InvalidValueException(ApiBaseException):
    def __init__(self, message, error_code):
        super().__init__(message, error_code, HTTPStatus.UNPROCESSABLE_ENTITY)
