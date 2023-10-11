class Signals(object):
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, Signal(*v) if isinstance(v, dict) else v)

    def __getattr__(self, item):
        return self.key.value

    def __setattr__(self, key, value):
        self.key.value = value

    def get(self, key):
        return self.__dict__[key]


class Signal():
    def __init__(self, value, db_number, offsetbyte, offsetbit):
        self.value = value
        self.db_number = db_number
        self.offsetbyte = offsetbyte
        self.offsetbit = offsetbit
