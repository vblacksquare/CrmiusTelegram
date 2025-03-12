
from typing import Any
import json


class BaseJsonifed:
    fields = []

    def to_dict(self):
        pass

    def to_json(self):
        return json.dumps(self.to_dict())


class JsonifiedProperty(BaseJsonifed):
    field = "base"

    def to_dict(self):
        try:
            return self.__getattribute__(self.field)

        except AttributeError:
            raise KeyError(f"Cant find field with name: {self.field} in object: {self}")


class Jsonified(BaseJsonifed):
    fields: list[str | JsonifiedProperty] = []

    def __process_dict(self, obj):
        res = {}

        for key in obj:
            if isinstance(obj[key], list):
                res.update({
                    key: self.__process_list(obj[key])
                })

            elif isinstance(obj[key], dict):
                res.update({
                    key: self.__process_dict(obj[key])
                })

            elif issubclass(obj[key].__class__, BaseJsonifed):
                res.update({
                    key: obj[key].to_dict()
                })

            else:
                res.update({
                    key: obj[key]
                })

        return res

    def __process_list(self, obj):
        res = []

        for i in obj:
            if isinstance(i, list):
                res.append(self.__process_list(i))

            elif isinstance(i, dict):
                res.append(self.__process_dict(i))

            elif issubclass(i.__class__, BaseJsonifed):
                res.append(i.to_dict())

            else:
                res.append(i)

        return res

    def to_dict(self) -> dict:
        export = {}

        for field in self.fields:

            if isinstance(field, str):
                try:
                    obj = self.__getattribute__(field)

                except AttributeError:
                    raise KeyError(f"Cant find field with name: {field} in object: {self}")

            else:
                obj = field

            if isinstance(obj, list):
                data = {
                    field: self.__process_list(obj)
                }

            elif isinstance(obj, dict):
                data = {
                    field: self.__process_dict(obj)
                }

            elif issubclass(obj.__class__, BaseJsonifed):
                data = {
                    field: obj.to_dict()
                }

            else:
                data = {
                    field: obj
                }

            export.update(data)

        return export

    def update(self, key: str, value: Any) -> None:
        try:
            obj = self.__getattribute__(key)

        except AttributeError:
            return

        if isinstance(obj, list):
            obj.append(value)

        else:
            obj.update({key: value})

    def to_str(self):
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            indent=4
        )
