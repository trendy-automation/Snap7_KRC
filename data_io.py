class Data_IO(dict):
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, Tag(*v, k))

    def get(self, key):
        return self.__dict__[key].value

    def set(self, key, value):
        self.__dict__[key].value = value

    #def keys(self):
    #    return self.__dict__.keys()

    def __ne__(self, other):
        return self.__dict__ != other.__dict__

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield value


class Tag:
    def __init__(self, value, value_type: str, offsetbyte: int, offsetbit: int, name: str):
        self.value = value
        self.value_type = value_type
        self.offsetbyte = offsetbyte
        self.offsetbit = offsetbit
        self.name = name

    def __eq__(self, other):
        return \
            self.value == other.value and \
            self.value_type == other.value_type and \
            self.offsetbyte == other.offsetbyte and \
            self.offsetbit == other.offsetbit and \
            self.name == other.name