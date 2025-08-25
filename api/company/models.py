import pynamodb.constants
from pynamodb.attributes import UnicodeAttribute
from util.pynamodb_util import DDBModel


class CompanyModel(DDBModel):
    """
    곧바로 사용 업체 정보 모델
    """

    class Meta:
        billing_mode = pynamodb.constants.PAY_PER_REQUEST_BILLING_MODE
        table_name = 'finance_backend_dev_companies'
        region = 'ap-northeast-2'


    # 기본 정보
    company_id = UnicodeAttribute(hash_key=True)
    company_name = UnicodeAttribute(null=False)
    company_type = UnicodeAttribute(null=False)