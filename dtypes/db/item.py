
from . import method
from utils.jsonify import Jsonified


class DatabaseItem(Jsonified):
    id: str
    methods: list[method.BaseDatabaseMethod] = [
        method.GetOne, method.GetMany,
        method.AddOne, method.AddMany,
        method.UpdateOne, method.UpdateMany,
        method.RemoveOne, method.RemoveMany
    ]

    @staticmethod
    def get_methods(item) -> dict:
        if not issubclass(item, DatabaseItem):
            raise TypeError(f"Can't get db methods from not DatabaseItem type, got {item}")

        return {
            item.__name__: {
                "methods": item.methods,
                "class": item
            },
            item: {
                "methods": item.methods,
                "class": item
            }
        }

    def __str__(self):
        return f"{self.__class__.__name__}(id='{self.id}')"
