
from utils.jsonify import BaseJsonifed


class BaseDatabaseMethod:
    name = "base"
    target: str
    data: object | dict
    to_update: list[str] | None

    def __init__(self, target, data=None, to_update=None, **kwargs):
        self.target = target
        self.to_update = to_update
        self.data = data if data else {}

        if isinstance(self.data, dict):
            unpacked = {}

            for key in kwargs:
                item = kwargs[key]

                if issubclass(item.__class__, BaseJsonifed):
                    item = item.to_dict()

                unpacked.update({key: item})

            self.data.update(unpacked)


class AddOne(BaseDatabaseMethod):
    name = "add_one"


class AddMany(BaseDatabaseMethod):
    name = "add_many"


class GetOne(BaseDatabaseMethod):
    name = "get_one"


class GetMany(BaseDatabaseMethod):
    name = "get_many"


class UpdateOne(BaseDatabaseMethod):
    name = "update_one"


class UpdateMany(BaseDatabaseMethod):
    name = "update_many"


class RemoveOne(BaseDatabaseMethod):
    name = "remove_one"


class RemoveMany(BaseDatabaseMethod):
    name = "remove_many"
