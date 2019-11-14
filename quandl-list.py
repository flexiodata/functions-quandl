# ---
# name: quandl-list
# deployed: true
# title: Quandl List Table
# description: Returns the contents of a table on Quandl
# params:
#   - name: name
#     type: string
#     description: The name of the table to return
#     required: true
#   - name: properties
#     type: array
#     description: The properties to return (defaults to all properties). The properties are the columns/headers of the table or series being requested. Use "*" to return everything.
#     required: false
# examples:
#   - '"HKEX/83079"'
#   - '"HKEX/83079", "*"'
#   - '"HKEX/83079", "date, nominal price, high, low"'
# notes: |
# ---

import json
import requests
import urllib
import itertools
from datetime import *
from decimal import *
from cerberus import Validator
from collections import OrderedDict

# main function entry point
def flexio_handler(flex):

    # get the api key from the variable input
    auth_token = dict(flex.vars).get('quandl_api_key')
    if auth_token is None:
       flex.output.content_type = "application/json"
       flex.output.write([[""]])
       return

    # get the input
    input = flex.input.read()
    try:
        input = json.loads(input)
        if not isinstance(input, list): raise ValueError
    except ValueError:
        raise ValueError

    # define the expected parameters and map the values to the parameter names
    # based on the positions of the keys/values
    params = OrderedDict()
    params['name'] = {'required': True, 'type': 'string', 'coerce': str}
    params['properties'] = {'required': False, 'validator': validator_list, 'coerce': to_list, 'default': '*'}
    input = dict(zip(params.keys(), input))

    # validate the mapped input against the validator
    # if the input is valid return an error
    v = Validator(params, allow_unknown = True)
    input = v.validated(input)
    if input is None:
        raise ValueError

    try:

        # make the request
        # see here for more info: https://docs.quandl.com/
        url_query_params = {"api_key": auth_token}
        url_query_str = urllib.parse.urlencode(url_query_params)

        url = 'https://www.quandl.com/api/v3/datasets/' + input['name'] + '?' + url_query_str
        headers = {
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers)
        content = response.json()

        # get the columns and rows; clean up columns by converting them to
        # lowercase and removing leading/trailing spaces
        rows = content.get('dataset',{}).get('data',[])
        columns = content.get('dataset',{}).get('column_names',[])
        columns = [c.lower().strip() for c in columns]

        # get the properties (columns) to return based on the input;
        # if we have a wildcard, get all the properties
        properties = [p.lower().strip() for p in input['properties']]
        if len(properties) == 1 and properties[0] == '*':
            properties = columns

        # build up the result
        result = []

        result.append(properties)
        for r in rows:
            item = dict(zip(properties, r)) # create a key/value for each column/row so we can return appropriate columns
            item_filtered = [item.get(p) or '' for p in properties]
            result.append(item_filtered)

        result = json.dumps(result, default=to_string)
        flex.output.content_type = "application/json"
        flex.output.write(result)

    except:
        raise RuntimeError

def validator_list(field, value, error):
    if isinstance(value, str):
        return
    if isinstance(value, list):
        for item in value:
            if not isinstance(item, str):
                error(field, 'Must be a list with only string values')
        return
    error(field, 'Must be a string or a list of strings')

def to_string(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (Decimal)):
        return str(value)
    return value

def to_list(value):
    # if we have a list of strings, create a list from them; if we have
    # a list of lists, flatten it into a single list of strings
    if isinstance(value, str):
        return value.split(",")
    if isinstance(value, list):
        return list(itertools.chain.from_iterable(value))
    return None

