#!/usr/bin/env python3
# coding: utf-8

import json
import re


class Typehandler:
    def __init__(self):
        self._encoders = {}
        self._decoders = {}

    @property
    def encoders(self):
        return  self._encoders

    @property
    def decoders(self):
        return self._decoders

    def register_enc(self, tp, name, func):
        self._encoders[name] = {"type": tp, "func": func}

    def register_dec(self, tp, name, func):
        self._decoders[name] = {"type": tp, "func": func}


_type_handler =  Typehandler()


def register_enc(tp, name, func):
    _type_handler.register_enc(tp, name, func)

def register_dec(tp, name, func):
    _type_handler.register_dec(tp, name, func)


import datetime

register_enc(datetime.datetime, "datetime", lambda x: x.strftime("%Y-%m-%d %H:%M:%S:%f"))
register_dec(datetime.datetime, "datetime", lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S:%f"))

register_enc(datetime.date, "date", lambda x: x.strftime("%Y-%m-%d"))
register_dec(datetime.date, "date", lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").date())


class CCJSONEncoder(json.JSONEncoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._encoders = _type_handler.encoders

    def default(self, obj):
        try:
            return super().default(self, obj)
        except TypeError:
            pass

        for name in self._encoders:
            tp = self._encoders[name]["type"]
            if type(obj) == tp:
                enc = self._encoders[name]["func"]
                data = enc(obj)
                return "#{}:{}".format(name, data)

        raise TypeError(repr(obj) + " is not JSON serializable")


class CCJSONDecoder(json.JSONDecoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._decoders = _type_handler.decoders
        self._typemarker = re.compile("^#[^:]+:")

    def decode(self, ss, **kwargs):
        js = super().decode(ss, **kwargs)
        return self._trans_type(js)

    def _trans_type(self, obj):
        if isinstance(obj, dict):
            return {o: self._trans_type(obj[o]) for o in obj}
        elif isinstance(obj, list):
            return [self._trans_type(o) for o in obj]
        elif isinstance(obj, str):
            m = self._typemarker.match(obj)
            if m:
                x = m.end()
                name = obj[1: x - 1]
                data = obj[x:]
                dec = self._decoders.get(name)
                if dec:
                    return  dec["func"](data)

        return obj


if __name__ == "__main__":
    class X:
        def __init__(self, x):
            self.x = x

        def __repr__(self):
            return "<X: {}>".format(self.x)

        def xx(self):
            return self.x

        def __eq__(self, other):
            return self.x == other.x


    register_enc(X, "X", lambda x: str(x.xx()))
    register_dec(X, "X", lambda x: X(int(x)))

    a = {
        "dt": datetime.datetime.now(),
        "x": {
            "1": "asd",
            "2": "#:sa",
            "3": "#as:",
            "4": "#as:sadf",
            "000000": datetime.datetime.now().date()
        },
        "ssss": [X(0), 11, X(2)]
    }
    print(a)

    b = json.dumps(a, cls=CCJSONEncoder, indent=4)
    print(b)

    c = json.loads(b, cls=CCJSONDecoder)
    print(c)

    d = json.dumps(c, cls=CCJSONEncoder, indent=4)
    print(d)

    print("a==c:", a == c)
