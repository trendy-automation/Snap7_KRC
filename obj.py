class Obj(object):
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, Obj(v) if isinstance(v, dict) else v)

    def __setattr__(self, key, value):
        # print(f'obj.py {key=}, {value=}')
        if not isinstance(value, list) and key in self.__dict__:
            self.__dict__[key][0] = value
        else:
            self.__dict__[key] = value

    def __getattr__(self, item):
        if isinstance(item, dict):
            return self.__dict__[item][0]
        elif item in ['__deepcopy__', '__setstate__']:
            return self.__dict__.__getattr__(item)
        else:
            return self.__dict__[item]

    def __iter__(self):
        return iter(self.__dict__.items())

    def get(self, item):
        return self.__dict__[item][0]
        # return self.__getattr__(item)
        # return self.__dict__[item]
        #return getattr(self, item)

    def set(self, key, value):
        self.__setattr__(key, value)
        # if key in self.__dict__ and not isinstance(value, list):
        #     self.__dict__[key][0] = value
        # else:
        #     self.__dict__[key] = value

    def signals(self):
        return self.__dict__.keys()
