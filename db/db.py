
import typing

import motor.motor_asyncio as motor
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

from loguru import logger as log

from utils.singleton import SingletonMeta
from dtypes.db import DatabaseItem
from dtypes.db import method as mth
from dtypes.response import BaseResponse, ErrResponse, OkResponse


class Db(metaclass=SingletonMeta):
    def __init__(self):
        self.classes = {}

        self.log = log.bind(classname=self.__class__.__name__)
        self.client: motor.AsyncIOMotorClient = None
        self.db: AsyncIOMotorDatabase = None

    def items(self) -> list[DatabaseItem]:
        res = []

        for obj in self.classes:
            if not isinstance(obj, str):
                res.append(obj)

        return res

    async def ex(
            self,
            method: typing.Type[mth.BaseDatabaseMethod]
    ) -> typing.Type[BaseResponse]:
        response = await self._ex(method)

        if response.status != "ok":
            self.log.warning(response)
            return None

        return response.data

    async def _ex(
            self,
            method: typing.Type[mth.BaseDatabaseMethod]
    ) -> typing.Type[BaseResponse]:

        if self.db is None:
            raise RuntimeError("Can't execute database method without connection")

        class_methods = self.classes.get(method.target)

        if not class_methods:
            raise NotImplementedError(f"{method.target.__name__} hasn't been added to db")

        if method.__class__ not in class_methods["methods"]:
            raise NotImplementedError(f"There is no {method.__class__.__name__} method for {method.target.__name__}")

        item_class = class_methods["class"]
        collection_name = item_class.__name__

        try:
            match method.name:
                case "add_one":
                    return await self.__add_one(collection_name, method.data)

                case "add_many":
                    return await self.__add_many(collection_name, method.data)

                case "get_one":
                    return await self.__get_one(collection_name, method.data, item_class)

                case "get_many":
                    return await self.__get_many(collection_name, method.data, item_class)

                case "update_one":
                    return await self.__update_one(collection_name, method.data, method.to_update)

                case "update_many":
                    return await self.__update_many(collection_name, method.data)

                case "remove_one":
                    return await self.__remove_one(collection_name, method.data)

                case "remove_many":
                    return await self.__remove_many(collection_name, method.data)

                case unsupported_method:
                    raise NotImplementedError(f"There is not such method {unsupported_method}")

        except Exception as err:
            self.log.exception(err)
            self.log.error(f"Cant execute {method}")

    def connect(
        self,
        name: str,
        uri: str
    ):
        if self.client:
            self.log.warning(f"Already connected to db")
            return

        for item in DatabaseItem.__subclasses__():
            self.__add_methods(DatabaseItem.get_methods(item))

        try:
            self.client = motor.AsyncIOMotorClient(uri)
            self.db = self.client[name]
            self.log.info("Connected to db")

        except Exception as err:
            self.log.exception(err)
            self.log.critical(f"Cant connect to db")
            exit()

    def __add_methods(
            self,
            class_method
    ):

        self.classes.update(class_method)
        self.log.debug(f"Added new methods {class_method}")

    async def __is_item(
            self,
            collection_name: str,
            item_id: str
    ) -> bool:

        collection: AsyncIOMotorCollection = self.db[collection_name]
        item = await collection.find_one({"id": item_id}, {"_id": 0})
        return not item is None

    async def __is_items(
            self,
            collection_name: str,
            item_ids: list[str]
    ) -> dict[str, bool]:
        resp = {
            item_id: False
            for item_id in item_ids
        }

        collection: AsyncIOMotorCollection = self.db[collection_name]
        items = collection.find({"id": {"$in": item_ids}}, {"_id": 0})

        async for i in items:
            resp.update({
                i['id']: True
            })

        return resp

    async def __add_one(
            self,
            collection_name: str,
            item: typing.Type[DatabaseItem]
    ) -> typing.Type[BaseResponse]:

        if not isinstance(item, DatabaseItem):
            return ErrResponse(f"item have to be type of {DatabaseItem}", data=item)

        if await self.__is_item(collection_name, item.id):
            return ErrResponse(f"Duplicate item: {item}", data=item)

        collection: AsyncIOMotorCollection = self.db[collection_name]
        response = await collection.insert_one(item.to_dict())

        return OkResponse(data={"db_answer": str(response)})

    async def __add_many(
            self,
            collection_name: str,
            items: typing.Type[DatabaseItem] | list[typing.Type[DatabaseItem]]
    ) -> typing.Type[BaseResponse]:

        if type(items) not in [list, tuple]:
            items = [items]

        for item in items:
            if not isinstance(item, DatabaseItem):
                return ErrResponse(f"Every item have to be type of {DatabaseItem}", data=items)

        is_items = await self.__is_items(collection_name, list(map(lambda x: x.id, items)))

        to_add = []
        for item in items:
            if is_items[item.id]:
                continue

            to_add.append(item.to_dict())

        if not len(to_add):
            return OkResponse(
                description=f"Added 0 items, duplicate: {len(items)} items"
            )

        collection: AsyncIOMotorCollection = self.db[collection_name]
        resps = []

        for row in to_add:
            try:
                response = await collection.insert_one(row)
                resps.append(response)

            except Exception as err:
                self.log.exception(err)
                resps.append(str(err))

        return OkResponse(
            description=f"Added {len(to_add)} items, duplicate: {len(items)-len(to_add)} items",
            data={
                "db_answers": resps
            }
        )

    async def __get_one(
            self,
            collection_name: str,
            query: typing.Type[DatabaseItem] | dict, item_class: type
    ) -> typing.Type[BaseResponse]:
        if isinstance(query, DatabaseItem):
            query = query.to_dict()

        collection: AsyncIOMotorCollection = self.db[collection_name]

        item = await collection.find_one(query, {"_id": 0})

        if not item:
            return OkResponse(description=f"No item found with {query = }")

        return OkResponse(data=item_class(**item))

    async def __get_many(
            self,
            collection_name: str,
            query: typing.Type[DatabaseItem] | dict,
            item_class: type
    ) -> typing.Type[BaseResponse]:
        if isinstance(query, DatabaseItem):
            query = query.to_dict()

        collection: AsyncIOMotorCollection = self.db[collection_name]
        items = collection.find(query, {"_id": 0})

        data = []
        async for i in items:
            data.append(item_class(**i))

        return OkResponse(data=data)

    async def __update_one(
            self,
            collection_name: str,
            item: typing.Type[DatabaseItem],
            to_update: list[str] | None
    ) -> typing.Type[BaseResponse]:

        if not isinstance(item, DatabaseItem):
            return ErrResponse(f"item have to be type of {DatabaseItem}", data=item)

        if not await self.__is_item(collection_name, item.id):
            return ErrResponse(f"There is not such item to update: {item}", data=item)

        collection: AsyncIOMotorCollection = self.db[collection_name]

        data = item.to_dict()
        if to_update:
            for field in list(data):
                if field not in to_update:
                    del data[field]

        response = await collection.update_one({"id": item.id}, {"$set": data})

        return OkResponse(data={"db_answer": str(response)})

    async def __update_many(
            self,
            collection_name: str,
            item: typing.Type[DatabaseItem]
    ) -> typing.Type[BaseResponse]:

        raise NotImplementedError()

    async def __remove_one(
            self,
            collection_name: str,
            item: typing.Type[DatabaseItem]
    ) -> typing.Type[BaseResponse]:

        if not isinstance(item, DatabaseItem):
            return ErrResponse(f"item have to be type of {DatabaseItem}", data=item)

        if not await self.__is_item(collection_name, item.id):
            return ErrResponse(f"There is not such item to remove: {item}", data=item)

        collection: AsyncIOMotorCollection = self.db[collection_name]
        response = await collection.delete_one({"id": item.id})

        return OkResponse(data={"db_answer": str(response)})

    async def __remove_many(
            self,
            collection_name: str,
            item: typing.Type[DatabaseItem]
    ) -> typing.Type[BaseResponse]:

        raise NotImplementedError()
