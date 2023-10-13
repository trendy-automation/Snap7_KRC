class Data_IO(dict):
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, Tag(*v, k))

    def get(self, key):
        return self.__dict__[key].value

    def set(self, key, value):
        self.__dict__[key].value = value

    def __iter__(self):
        return iter(self.__dict__.values())

class Tag:
    def __init__(self, value, value_type: str, offsetbyte: int, offsetbit: int, name: str):
        self.value = value
        self.value_type = value_type
        self.offsetbyte = offsetbyte
        self.offsetbit = offsetbit
        self.name = name
    def __set__(self, instance, value):
        if isinstance(value, Tag):
            self.value = value.value
        else:
            instance.value = value

    # def __get__(self, instance, owner):
    #     return instance.value