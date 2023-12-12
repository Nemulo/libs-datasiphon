# start with mongoDB
from .base import QueryBuilder, FilterFormatError, FilterColumnError, InvalidOperatorError, InvalidValueError
import pymongo.collection as pc
import pymongo.cursor as pcur
import typing as t


class Mongo(QueryBuilder):
    """
    Mongo query builder
    """
    @staticmethod
    def get_arg(model: dict) -> t.Tuple[str, t.Any]:
        """
        Yield the first key-value pair of a dict for mongo document filter

        :param model: The model to get the argument from

        :return: The first key-value pair of the model
        """
        for key, value in model.items():
            if not isinstance(value, dict):
                if key in Mongo.OPS:
                    yield (None, {f'${key}': value})
                else:
                    yield (key, value)
            else:
                for k, v in Mongo.get_arg(value):
                    if k is None:
                        yield (key, v)
                    else:
                        yield (f'{key}.{k}', v)

    @staticmethod
    def validate_fmt(model: dict) -> tuple[dict, dict]:
        """
        Validate the format of the model, also transform operators in model into mongo-filter operators

        :param model: The model to validate

        :return: The validated and transformed model
        """
        kw = Mongo.get_kw(model)
        args = {
            processed_key: processed_value for processed_key, processed_value in Mongo.get_arg(model)
        }
        return args, kw

    @staticmethod
    def get_kw(model: dict) -> dict:
        """
        Get the keyword arguments from the model

        :param model: The model to get the keyword arguments from

        :return: The keyword arguments
        """
        kw = {}
        for key, value in model.items():
            if key in Mongo.KW:
                kw[key] = Mongo._kw(key, value)
        for key in kw:
            del model[key]  # noqa
        return kw

    @classmethod
    def build(cls, collection: pc.Collection, model: dict, projection: dict = None) -> pcur.Cursor:
        """
        Build a Mongo query from a model

        :param model: The model to build from

        :raises FilterFormatError: If the model has an invalid format
        :raises InvalidOperatorError: If the model has an invalid operator
        :raises InvalidValueError: If the model has an invalid value

        :return: The built query
        """
        raise NotImplementedError()  # Noqa
        if not isinstance(collection, pc.Collection):
            raise TypeError(f"Invalid collection: {collection}")
        parsed_model, kw = cls.validate_fmt(model)
        cursor = collection.find(parsed_model, projection=projection).sort(
            kw.get('order_by', {})).skip(kw.get('offset', 0)).limit(kw.get('limit', 0))
        return cursor

    @classmethod
    def _kw(cls, key: str, value: t.Any) -> t.Any:
        return getattr(cls, key)(value)

    @staticmethod
    def order_by(value: dict) -> t.Any:
        """
        Transform an order_by model into a mongo sort

        :param value: The value to transform

        :return: The transformed value
        """
        order_dict = {}
        if not isinstance(value, dict):
            raise FilterFormatError(f"Invalid format: order_by -> {value}")
        ordering = {
            'asc': 1,
            'desc': -1
        }
        try:
            for direction, col in value.items():
                order_dict[col] = ordering[direction]
        except KeyError:
            raise InvalidValueError(f"Invalid value: order_by -> {value}")
        return order_dict

    @staticmethod
    def limit(value: int) -> int:
        """
        Transform a limit model into a mongo limit

        :param value: The value to transform

        :return: The transformed value
        """
        if not isinstance(value, int):
            raise InvalidValueError(f"Invalid value: limit -> {value}")
        return value

    @staticmethod
    def offset(value: int) -> int:
        """
        Transform an offset model into a mongo offset

        :param value: The value to transform

        :return: The transformed value
        """
        if not isinstance(value, int):
            raise InvalidValueError(f"Invalid value: offset -> {value}")
        return value
