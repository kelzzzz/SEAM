import pybinn
from schema import Schema

class BinnHelper:
    @staticmethod
    def pack(obj: Schema) -> bytes:
        fields = obj.__annotations__.keys()
        data_dict = {field: getattr(obj, field) for field in fields}
        return pybinn.dumps(data_dict)

    @staticmethod
    def unpack(binary_data: bytes, schema_cls: type):
        data_dict = pybinn.loads(binary_data)
        return schema_cls(**data_dict)