# ---
# name: quandl-table
# deployed: true
# title: Quandl Table
# description: Returns the contents of a table on Quandl
# params:
#   - name: name
#     type: string
#     description: The name of the table to return
#     required: true
#   - name: properties
#     type: array
#     description: The properties to return (defaults to all properties). The properties are the columns/headers of the table being requested. Use "*" to return everything.
#     required: false
#   - name: filter
#     type: string
#     description: Filter to apply with key/values specified as a URL query string. The keys allowed are table-dependent; see the Quandl documentation for each table to find out the filter parameters that are allowed. If a filter isn't specified, all the results up to the maximum result limit will be returned.
#     required: false
# examples:
#   - '"SHARADAR/SF3"'
#   - '"SHARADAR/SF3", "*", "ticker=AAPL"'
#   - '"SHARADAR/SF3", "*", "investorname=VANGUARD GROUP INC"'
#   - '"SHARADAR/SF3", "*", "ticker=AAPL,MSFT&investorname=VANGUARD GROUP INC"'
# notes: |
#   Results are limited to 100k rows.
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
    params['filter'] = {'required': False, 'type': 'string', 'coerce': str, 'default': ''}

    input = dict(zip(params.keys(), input))

    # validate the mapped input against the validator
    # if the input is valid return an error
    v = Validator(params, allow_unknown = True)
    input = v.validated(input)
    if input is None:
        raise ValueError

    table_name = input['name']
    table_properties = input['properties']
    table_filter = input['filter']

    result = []
    cursor_id = False
    page_idx = 0
    max_pages = 10

    while True:

        page_result = getTablePage(auth_token, table_name, table_properties, table_filter, cursor_id)
        if len(page_result['data']) > 0:
            result += page_result['data']

        cursor_id = page_result['cursor']
        if cursor_id is None or page_idx >= max_pages:
            break
        page_idx = page_idx + 1

    result = json.dumps(result, default=to_string)
    flex.output.content_type = "application/json"
    flex.output.write(result)

def getTablePage(auth_token, table_name, table_properties, table_filter, cursor_id):

    try:
        # get any optional filter
        filter = urllib.parse.parse_qs(table_filter)
        if filter is None:
            filter = {}

        # build up the query string and make the request
        # see here for more info: https://docs.quandl.com/
        url_query_params = {}

        # note: in quandl api, filters are tables are specified as url query params;
        # multiple values per key are specified as delimited list; e.g. ticker=AAPL,GOOG
        # following logic converts multiple items with the same key to a delimited list
        # as well as passes through multiple value per a single key:
        # * ticker=AAPL&ticker=GOOG => ticker=AAPL,GOOG
        # * ticker=AAPL,GOOG => ticker=AAPL,GOOG
        for filter_key, filter_list in filter.items():
            url_query_params[filter_key] = ",".join(filter_list)
        url_query_params['api_key'] = auth_token
        url_query_params['qopts.per_page'] = 10000
        url_query_str = urllib.parse.urlencode(url_query_params)

        # make the request
        # see here for more info: https://docs.quandl.com/
        url = 'https://www.quandl.com/api/v3/datatables/' + table_name + '?' + url_query_str
        headers = {
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers)
        content = response.json()

        # get the cursor
        next_cursor_id = content.get('meta',{}).get('next_cursor_id')

        # get the columns and rows; clean up columns by converting them to
        # lowercase and removing leading/trailing spaces
        rows = content.get('datatable',{}).get('data',[])
        columns = content.get('datatable',{}).get('columns',[])
        columns = [c.get('name','').lower().strip() for c in columns]

        # get the properties (columns) to return based on the input;
        # if we have a wildcard, get all the properties
        properties = [p.lower().strip() for p in table_properties]
        if len(properties) == 1 and properties[0] == '*':
            properties = columns

        # get any optional filter
        filter = table_filter
        filter = urllib.parse.parse_qs(filter)
        if len(filter) == 0:
            filter = None

        # build up the result
        data = []

        # if the input cursor_id is False, we're on the first row, so include the columns
        # on subsequent requests, the cursor_id will be either a string or None
        if cursor_id is False:
            data.append(properties)

        # append the rows
        for r in rows:
            item = dict(zip(columns, r)) # create a key/value for each column/row so we can return appropriate columns
            item_filtered = [item.get(p) or '' for p in properties]
            data.append(item_filtered)

        return {"data": data, "cursor": next_cursor_id}

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

def to_date(value):
    # if we have a number, treat it as numeric date value from
    # a spreadsheet (days since 1900; e.g. 1 is 1900-01-01)
    if isinstance(value, (int, float)):
        return datetime(1900,1,1) + timedelta(days=(value-1))
    if isinstance(value, str):
        return datetime.strptime(value, '%Y-%m-%d')
    return value

