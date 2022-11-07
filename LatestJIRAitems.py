#!/usr/local/bin/python3

import argparse
import base64
import datetime
import json
import pathlib
import urllib.request
from sys import argv

"""
A script that gets one's latest JIRA items with various configuration options.
"""

jira_subdomain = 'playerlync'  # Often one's company's custom subdomain. Becomes {jira_subdomain}.attlasian.net
default_credential_file = '~/.config/pr_script/authorization_token.txt'  # Can be overrriden by the -C argument`
default_days_historic = 7  # Can be overwritten by the -D or -H arguments


# GET/SET NECESSARY RUN-SPECIFIC VARIABLES...
parser = argparse.ArgumentParser(
    description=f"Get 'my' JIRA items that have had activity on them in the last {default_days_historic} days"
)
parser.add_argument(
    '--credential_file', '-C',
    required=False,
    type=str,
    help='Location of your credential file. If you do not have one already,  - Instructions here:\n'
         'https://blog.developer.atlassian.com/creating-a-jira-cloud-issue-in-a-single-rest-call/\n\n'
         'Follow steps 1 and 2 and put the result in ~/.config/pr_script/authorization_token.txt using '
         'the following pattern:\n'
         '<your PlayerLync.com email address>:<API Token value>'
)
parser.add_argument(
    '--include_epics', '-E',
    required=False,
    action='store_const',
    const=1,
    default=0,
    help='Include Epics - without this, Epics are not shown'
)
parser.add_argument(
    '--include_improvements', '-I',
    required=False,
    action='store_const',
    const=1,
    default=0,
    help='Include Improvements - without this, Improvement-type items are not shown'
)
parser.add_argument(
    '--include_resolved_items', '-R',
    required=False,
    action='store_const',
    const=1,
    default=0,
    help='Include items that HAVE been resolved (usually Done or Rejected)'
)
parser.add_argument(
    '--all_historic', '-H',
    required=False,
    action='store_const',
    const=1,
    default=0,
    help=f'Include ALL Items, not just the last {default_days_historic} days'
)
parser.add_argument(
    '--last_days', '-D',
    required=False,
    type=int,
    help=f'How many days of modified items to include (without this, the default of {default_days_historic} is used)'
)
parser.add_argument(
    '--hide_worklog_entries', '-W',
    required=False,
    action='store_const',
    const=1,
    default=0,
    help=f'If set, will NOT show all of the work-logged entries for each given item.'
)
args = parser.parse_args()
show_worklog = not args.hide_worklog_entries

def print_item(jira_item: dict):
    """Print `jira_item`"""
    total_time = f"{jira_item['total_time'][0]:02d}:{jira_item['total_time'][1]:02d}:{jira_item['total_time'][2]:02d}"
    print(
        f"Key: {jira_item['key']} ({jira_item['issue_type']}) :: URL: {jira_item['url']}\n"
        f"Summary: {jira_item['summary']}\n"
        f"Status: {jira_item['status']}\n"
        f"Last Updated: {jira_item['last_updated'].strftime('%Y-%m-%d %H:%M:%S %z (%a)')}\n"
        f"Total Time Tracked to this Item: {tuple_to_string(human_readable_from_seconds(jira_item['item_seconds_sum']))}"
    )
    this_item_time = 0
    if show_worklog and len(jira_item['time_entries']) > 0:
        for timestamp, timestring in jira_item['time_entries'].items():
            if sum(timestring) > 0:
                timestamp_string = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%Y-%m-%d %H:%M:%S (%a)')
                print(f"\t{timestamp_string}: Time logged = {tuple_to_string(timestring)}")
    print("\n")


def human_readable_from_seconds(seconds: int) -> (int, int, int):
    """ Convert seconds to hours, minutes and seconds"""
    total_hours = 0
    total_minutes = 0
    total_seconds = 0
    if seconds:
        total_hours: int = seconds // 3600
        total_minutes_raw = 60 * ((seconds / 3600) - total_hours)
        total_seconds: int = round(60 * (total_minutes_raw - int(total_minutes_raw)))
        total_minutes: int = round(total_minutes_raw)

    return total_hours, total_minutes, total_seconds

def tuple_to_string(tuple_in: tuple) -> str:
    return f"{tuple_in[0]:02d}:{tuple_in[1]:02d}:{tuple_in[2]:02d}"

# Get JIRA data
credential_file = args.credential_file or default_credential_file
credential_file = credential_file.replace('~', str(pathlib.Path.home()))
if not pathlib.Path(credential_file).is_file():
    print(
        f"Must have a credential file here: {credential_file}\nFile must contain one line: email:token\nUse -h flag for"
        f" more details"
    )
    exit(1)
with open(credential_file, 'r') as handle:
    credentials = handle.readline().strip()
if not credentials:
    print(f"Tried to read first line from credential file '{credential_file}' which is empty. Cannot continue.")
    exit(2)

# Get 'currentUser' info
jira_url = f'https://{jira_subdomain}.atlassian.net/rest/api/2/myself'
jira_headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': f'Basic {base64.urlsafe_b64encode(credentials.encode()).decode()}'
}
try:
    req = urllib.request.Request(method='GET', url=jira_url, headers=jira_headers)
    with urllib.request.urlopen(req) as result:
        data = json.loads(result.read().decode())
        status = result.status
        if status != 200:
            print(f'Failure to get data from JIRA. Response ({status}):\n{result.read().decode()}')
            exit(3)
except Exception as url_error:
    print(f'Failure to make GET {jira_url} request to JIRA: {url_error}')
    exit(4)

if not data:
    print(f'No valid JSON data returned for GET {jira_url}. Weird.\nHere is the response data:\n{result.read().decode()}')
    exit(5)

my_acct_id = data.get('accountId')
if not my_acct_id:
    print(f'No "accountId" returned in the `data` for GET {jira_url}.\nHere is the `data` value:\n{data}')
    exit(6)


# Generate JQL
jql = '(worklogAuthor = currentUser() OR assignee = currentUser())'
if not args.include_resolved_items:
    jql += ' AND resolution = Unresolved'
if not args.all_historic:
    jql += f' AND updated > -{args.last_days or default_days_historic}d'

do_not_include_types_list = []
if not args.include_epics:
    do_not_include_types_list.append('epic')
if not args.include_improvements:
    do_not_include_types_list.append('improvement')
if len(do_not_include_types_list) > 0:
    jql += f' AND type NOT IN ({", ".join(do_not_include_types_list)})'

jql += ' ORDER BY updated DESC'

# Run the HTTP request
jira_url = f'https://{jira_subdomain}.atlassian.net/rest/api/2/search'
jira_headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': f'Basic {base64.urlsafe_b64encode(credentials.encode()).decode()}'
}
jira_data = "{"
jira_data += f"""
"jql": "{jql}",
"fields": [
  "summary",
  "timespent",
  "updated",
  "status",
  "issuetype"
],
"expand": [ "changelog" ],
"maxResults": 50
"""
jira_data += "}"

try:
    req = urllib.request.Request(method='POST', url=jira_url, headers=jira_headers, data=jira_data.encode())
    with urllib.request.urlopen(req) as result:
        data = json.loads(result.read().decode())
        status = result.status
        if status != 200:
            print(f'Failure to get data from JIRA. Response ({status}):\n{result.read().decode()}')
            exit(7)
except Exception as url_error:
    print(f'Failure to make request GET {jira_url} to JIRA: {url_error}')
    exit(8)

if not data:
    print(f'No valid JSON data returned for GET {jira_url}. Weird.\nHere is the response data:\n{result.read().decode()}')
    exit(9)

# Process JIRA data
total_time_logged = 0
items = {}
for item in data.get('issues', []):
    issue_type = item.get('fields', {}).get('issuetype', {}).get('name', 'Unknown Issue Type')
    status = item.get('fields', {}).get('status', {}).get('name', '-- Status Unknown --')
    key = item['key']
    url = f'https://playerlync.atlassian.net/browse/{key}'
    summary = item.get('fields', {}).get('summary')
    last_updated = datetime.datetime.strptime(
        item.get('fields', {}).get('updated'),
        '%Y-%m-%dT%H:%M:%S.%f%z'
    )

    time_spent_string = human_readable_from_seconds(item.get('fields', {}).get('timespent') or 0)

    time_entries = {}
    item_time_sum = 0
    for entry in item.get('changelog', {}).get('histories', []):
        if len(entry.get('items')) > 0 and entry.get('author', {}).get('accountId') == my_acct_id:
            change_timestamp = entry.get('created')
            for timespent in [r for r in entry.get('items') if r['field'] == 'timespent']:
                row_seconds = int(timespent.get('to') or 0) - int(timespent.get('from') or 0)
                time_entries[change_timestamp] = human_readable_from_seconds(row_seconds)
                item_time_sum += row_seconds

    items[key] = {
        'key': key,
        'issue_type': issue_type,
        'url': url,
        'summary': summary,
        'status': status,
        'last_updated': last_updated,
        'last_updated_epoch': last_updated.timestamp(),
        'total_time': time_spent_string,
        'time_entries': dict(sorted(time_entries.items())),
        'item_seconds_sum': item_time_sum
    }
    total_time_logged += item_time_sum

# All items if so configured
print(f"\nYOUR {len(items)} ITEMS", end='')
if not args.all_historic:
    print(f" FROM THE PAST {args.last_days or default_days_historic} DAYS:\n")
else:
    print(f" FROM ALL TIME:\n")

for item in items.values():
    print_item(item)
print()
print(f"\nTotal Time across all the items above: {tuple_to_string(human_readable_from_seconds(total_time_logged))}\n")

