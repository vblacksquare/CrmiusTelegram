
from utils.jsonify import Jsonified


class BaseResponse(Jsonified):
    status: str = "base"
    description: str = "base"
    data: dict | object | None = None

    def __init__(self, description: str = None, data: dict | object | None = None):
        self.status = self.status
        self.description = description if description else self.description
        self.data = self.data if data is None else data

        self.fields = ["status", "description", "data"]

    def __str__(self):
        return f"{self.__class__.__name__}(description=\"{self.description}\", data={self.data})"

    def is_err(self):
        return self.status == "err"

    def is_ok(self):
        return self.status == "ok"


from .response import OkResponse, ErrResponse
