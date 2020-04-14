#!/usr/bin/env python
# encoding: utf-8

from flask import Flask
from flask import request
from flask import Response
from functools import wraps
from collections import OrderedDict
import json

app = Flask(__name__)

listen = '0.0.0.0'
port = 10081
processes = 4

std_out = OrderedDict()
std_out['ret'] = 200
std_out['data'] = None
std_out['msg'] = None


def json_output(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        stand = std_out.copy()
        if type(result) == list or type(result) == tuple:
            try:
                stand['ret'] = int(result[0])
            except IndexError:
                stand['ret'] = 500
                stand['data'] = None
                stand['msg'] = "return String error"
                return json.dumps(stand)
            try:
                stand['data'] = result[1]
            except IndexError:
                pass
            try:
                stand['msg'] = result[2]
            except IndexError:
                pass
        else:
            stand['data'] = result
        result = json.dumps(stand)
        return Response(result, mimetype='application/json', status=stand['ret'])
    return wrapper


@app.route("/tester.json", methods=['GET', 'POST'])
@json_output
def test_input():
    content = request.get_json(force=True, silent=True, cache=False)
    app.logger.info("json: %s" % content)
    return "OK"


if __name__ == '__main__':
    app.run(host=listen, port=port, debug=True, threaded=True)