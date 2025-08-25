# Finance Backend API
금융 서비스 시스템(Finance Backend)을 위한 Flask 기반 백엔드 API 서비스

## 1. 프로젝트 구성
### 1.1 패키지 구조
    ├── api: 금융 서비스 시스템 백엔드 API의 최상단 패키지로 Flask와 공통(common) 객체를 초기화한다.
    │   └── company: 회사 정보 관리 API 패키지
    └── util: 유틸리티 모듈을 포함한다.

### 1.2 소스 구조
    ├── README.md
    ├── api
    │   ├── __init__.py
    │   ├── company
    │   │   ├── __init__.py
    │   │   ├── controllers.py: 회사 정보 관리 API 컨트롤러
    │   │   ├── models.py: 회사 정보 관련 모델
    │   │   └── services.py: 회사 정보 관련 서비스 로직
    │   └── common.py: api 패키지 전체에서 사용할 공통 객체를 포함하는 모듈
    ├── config.py: 각 배포 환경에 필요한 프레임워크 및 패키지들의 설정값을 담고 있는 모듈
    ├── contants.py: 공통으로 사용한 상수값의 모음
    ├── exceptions.py: 예외 클래스들의 모음
    ├── requirements.txt: 백엔드 API에 필요한 패키지들의 모음
    ├── util
    │   ├── __init__.py
    │   ├── file_utils.py: 파일 관련 유틸리티
    │   ├── jwt_utils.py: JWT 관련 유틸리티
    │   ├── logging_util.py: 로깅 관련 유틸리티
    │   ├── model_utils.py: 모델 관련 유틸리티
    │   ├── notification_utils.py: 알림 관련 유틸리티
    │   ├── pynamodb_util.py: PynamoDB 관련 유틸리티
    │   ├── rest_utils.py: REST API 관련 유틸리티
    │   ├── s3_utils.py: AWS S3 관련 유틸리티
    │   ├── social_signin_util.py: 소셜 로그인 관련 유틸리티
    │   └── time_utils.py: 날짜와 시간 관련 유틸리티
    ├── wsgi.py: 플라스크 애플리케이션 모듈(실행 엔트리 포인트)
    └── zappa_settings.json: zappa 설정 파일

### 1.3 api 패키지 구조
API는 api 패키지 아래에 서비스명으로 개별 패키지를 생성하고, 그 개별 패키지에 controllers, services, models 등의 모듈을 생성하여 개발한다.
    
    controllers: API를 노출하는 컨트롤러 모듈로 입력/출력값 변환과 유효성 검사 및 입력/출력 구조의 명세화(swagger)
    services: API에 필요한 서비스 로직을 포함하는 모듈
    models: value 객체나 ORM 관련 모델 객체를 포함하는 모듈
    tasks: 스케쥴 방식(cron)으로 실행한 함수를 포함하는 모듈(zappa에 events로 등록한다)
    routers: 외부 API 및 다른 서비스를 API로 호출하는 함수를 포함하는 모듈

## 2. 주요 제공 기능
* Flask-Restx 기반 REST API 개발 및 문서화 가능
* JWT 기반 토큰 인증 방식 지원(scope 클레임을 통해 권한 관리 가능)
* 금융 서비스 시스템 회사 정보 관리 API 제공
* 소셜 로그인(Google, Firebase) 인증 지원
* AWS S3를 이용한 파일 관리 유틸리티
* PynamoDB를 통한 DynamoDB ORM 지원
* Zappa를 이용해 AWS APIGateway 및 Lambda로 빠르고 간편한 배포 가능

## 3. 개발 및 배포
    1. Flask 기반의 API로 금융 서비스 시스템 백엔드 데이터를 제공한다.
       제공하는 API는 아래의 swagger URL에서 확인할 수 있다.

        https://finance-backend.52g.studio/swagger

        금융 서비스 시스템(Finance Backend) API는 finance-backend 도메인명으로 등록되어 있다.

    2. 배포는 Zappa를 이용하여 AWS의 API Gateway와 Lambda에 서버리스 형태로 배포된다.
    3. 소소 코드 변경 후, 프로젝트 루트 디렉토리에서 아래의 명령을 이용하여 배포한다.
        
        zappa update {개발 환경}

        zappa update dev
    
    4.  배포 상태 및 로그를 보려면 아래 명령으로 확인한다.
        
        zappa tail # 전체 로그 확인

        zappa tail --since 1h  # 1시간 이내의 로그만 확인
        zappa tail --since 5m  # 5분 이내의 로그만 확인


