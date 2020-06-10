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
import urllib
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import itertools
from datetime import *
from decimal import *
from cerberus import Validator
from collections import OrderedDict

# main function entry point
def flexio_handler(flex):

    # configuration
    max_rows_to_return = 1 # maximum rows to return

    # get the api key from the variable input
    auth_token = dict(flex.vars).get('quandl_api_key')
    if auth_token is None:
        raise ValueError

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

    name = input['name']
    filter = input['filter']
    properties = [p.lower().strip() for p in input['properties']]

    # get the result
    result = []

    current_row = 0
    for r in getRows(auth_token, name, filter):

        if current_row >= max_rows_to_return:
            break

        # get the row
        columns, row = r['columns'], r['row']
        if len(properties) == 1 and properties[0] == '*':
            properties = columns

        # if we're on the first row, append the columns
        if current_row == 0:
            result.append(properties)

        # if we don't have any row data, we're done
        if row is None:
            break

        item = dict(zip(columns, row)) # create a key/value for each column/row so we can return appropriate columns
        item_selected = [item.get(p) or '' for p in properties]
        result.append(item_selected)
        current_row = current_row + 1

    result = json.dumps(result, default=to_string)
    flex.output.content_type = "application/json"
    flex.output.write(result)

def getRows(auth_token, table_name, table_filter):

    # see here for more info: https://docs.quandl.com/

    # configure the basic query paraemters
    url_query_params = {}
    url_query_params['api_key'] = auth_token
    url_query_params['qopts.per_page'] = 5000

    # note: in quandl api, filters are tables are specified as url query params;
    # multiple values per key are specified as delimited list; e.g. ticker=AAPL,GOOG
    # following logic converts multiple items with the same key to a delimited list
    # as well as passes through multiple value per a single key:
    # * ticker=AAPL&ticker=GOOG => ticker=AAPL,GOOG
    # * ticker=AAPL,GOOG => ticker=AAPL,GOOG
    filter = urllib.parse.parse_qs(table_filter)
    if filter is None:
        filter = {}
    for filter_key, filter_list in filter.items():
        url_query_params[filter_key] = ",".join(filter_list)

    cursor_id = None
    while True:

        # if we have a cursor, add it to get the next page
        if cursor_id is not None:
            url_query_params['qopts.cursor_id'] = cursor_id

        # make the request
        url_query_str = urllib.parse.urlencode(url_query_params)
        url = 'https://www.quandl.com/api/v3/datatables/' + table_name + '?' + url_query_str
        headers = {
            'Accept': 'application/json'
        }
        response = requests_retry_session().get(url, headers=headers)
        response.raise_for_status()
        content = response.json()

        # get the columns and rows; clean up columns by converting them to
        # lowercase and removing leading/trailing spaces
        rows = content.get('datatable',{}).get('data',[])
        columns = content.get('datatable',{}).get('columns',[])
        columns = [c.get('name','').lower().strip() for c in columns]

        if len(rows) == 0:
            return {'columns': columns, 'row': None, }
        for r in rows:
            yield {'columns': columns, 'row': r}

        # get the cursor; if the cursor is None, there's no more items
        cursor_id = content.get('meta',{}).get('next_cursor_id')
        if cursor_id is None:
                return

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(429, 500, 502, 503, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

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

