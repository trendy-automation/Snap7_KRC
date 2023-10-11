class Obj(object):
    def __init__(self, d):
        for k, v in d.items():
            #setattr(self, k, Signal(*v) if isinstance(v, dict) else v)
            setattr(self, k, Obj(v) if isinstance(v, dict) else v)

    def __setattr__(self, key, value):
        if key in self.__dict__ and not isinstance(value, list):
            #setattr(self, key[0], value)
            self.__dict__[key][0] = value
        else:
            self.__dict__[key] = value

    def __getattr__(self, item):
        #return getattr(self, item[0])
        return self.__dict__[item][0]

    def __iter__(self):
        return iter(self.__dict__)

    def get(self, item):
        return getattr(self, item)
        #return self.__dict__[item]

    def signals(self):
        return self.__dict__.keys()


    # def __ne__(self, other):
    #     return not self.__eq__(other)
    #
    # def __eq__(self, other):
    #     result = False
    #     if isinstance(self, list) and isinstance(other, list) and len(self) == len(other):
    #         result = all(i == j for i, j in zip(self, other))
    #     elif isinstance(self, dict) and isinstance(other, dict):
    #         if set(self.__dict__.keys()) == set(other.__dict__.keys()):
    #             result = all(i == j for i, j in zip(self.__dict__.iteritems(), other.__dict__.iteritems()))
    #     return result

        #def __set__(self, instance, value):
    #    if isinstance(instance, list) and isinstance(value, list):
    #        instance = value
    #    elif isinstance(instance, dict) and isinstance(value, dict):
    #            keys = set(instance.__dict__.keys()) & set(value.__dict__.keys())
    #            for key in keys():
    #                instance.__setattr__(key, value.__getattribute__(key))
