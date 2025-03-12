
from . import BaseResponse


class OkResponse(BaseResponse):
    status = "ok"
    description = "ok"


class ErrResponse(BaseResponse):
    status = "err"
    description = "err"
