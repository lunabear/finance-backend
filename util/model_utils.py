"""
    Data Model 처리 관련된 유틸리티 모듈
"""


def update_model_from_args(model, args, excluded_keys=None, ignore_none=True):
    """
    dictionary 형태로 넘어온 request의 key와 model에 있는 attribute와 같으면 해당 값을 attribute의 value로 설정한다.
    :param model: args의 Key-value로 매핑될 model
    :param args: dictionary 형태의 모델
    :param excluded_keys: 수정에서 제외할 키 목록. None이면 args의 모든 키-밸류로 모델을 업데이트 한다
    :param ignore_none : None 값 무시 여부 True 무시
    :return :
    """

    if excluded_keys:
        items = [x for x in args.items() if x[0] not in excluded_keys]
    else:
        items = [x for x in args.items()]

    changed = False
    for attr, value in items:
        if ignore_none and value is None:
            continue

        if getattr(model, attr) != value:
            setattr(model, attr, value)
            changed = True

    return changed


def deserialize_pynamo_model(pynamo_models):
    """
    pynamodb에서 query나 scan으로 얻은 페이징 모델을 리스트 형태로 변환
    :param pynamo_models: pynamodb 모델
    :return:
    """
    return list(pynamo_models)


def get_total_count_pynamo_models(pynamo_models):
    """
    pynamodb에서 query나 scan으로 얻은 페이징 모델의 건수를 반환
    :param pynamo_models: pynamodb 모델
    :return:
    """
    return len(deserialize_pynamo_model(pynamo_models))