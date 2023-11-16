from datetime import datetime, timedelta, timezone
import re
import requests
import subprocess
from typing import NamedTuple

class FeatureGate(NamedTuple):
    id: str
    version: str
    testnet: str
    devnet: str
    desc: str
    issue_link: str
    owner: str


def get_next_n_epoch_starts(current_epoch, time_remaining, epoch_duration, n):
    '''Return an array of tuples (epoch #, datetime) of future epoch starts'''
    # print("current epoch: {}\ntime remaining: {}\nepoch duration: {}\nn: {}\n".format(current_epoch, time_remaining, epoch_duration, n))
    result = []
    if n < 1 or n > 100:
        return result
    
    next_epoch = current_epoch + 1
    next_boundary = datetime.now(timezone.utc) + time_remaining
    result.append((next_epoch, next_boundary))
    for i in range(n-1):
        next_epoch = next_epoch + 1
        next_boundary = next_boundary + epoch_duration
        result.append((next_epoch, next_boundary))
    return result

## Remaining: 17h 39m 23s failed
def parse_time_string(input):
    '''Parse strings like 1day 10h 18m 6s and return a timedelta.'''
    pattern = re.compile(r'((?P<day>\d+)days?)?( ?(?P<hour>\d+)h)?( ?(?P<min>\d+)m)?( ?(?P<sec>\d+)s)?')
    match_result = pattern.search(input)
    # print(match_result.group('day'))
    # print(match_result.group('hour'))
    # print(match_result.group('min'))
    # print(match_result.group('sec'))
    days = int(match_result.group('day')) if match_result.group('day') else 0
    hours = int(match_result.group('hour')) if match_result.group('hour') else 0
    minutes = int(match_result.group('min')) if match_result.group('min') else 0
    seconds = int(match_result.group('sec')) if match_result.group('sec') else 0
    delta = timedelta(
        days=days,
        hours=hours,
        seconds=seconds,
        minutes=minutes,
    )
    # print(delta)
    return delta

def get_recent_and_pending(cluster):
    status = subprocess.run(['solana', 'feature', 'status', '-u'+ cluster, '--display-all'], stdout=subprocess.PIPE)
    status_text = str(status.stdout).replace(r'\n', '\n')
#     status_text = '''9gxu85LYRAcZL38We8MYJ4A9AwgBBPtVBAqebMcT1241 | active since epoch 489  | 205724256       | cap accounts data allocations per transaction #27375
# A16q37opZdQMCbe5qJ6xpBB9usykfv8jZaMkxvZQi4GJ | active since epoch 490  | 206156264       | add alt_bn128 syscalls #27961
# 8Zs9W7D9MpSEtUWSQdGniZk2cNmV22y6FLJwCx53asme | active since epoch 492  | 207020260       | enable bpf upgradeable loader ExtendProgram instruction #25234
# SVn36yVApPLYsa8koK3qUcy14zXDnqkNYWyUh1f4oK1  | pending until epoch 493 | NA              | ignore slot when calculating an account hash #28420
# SVn36yVApPLYsa8koK3qUcy14zXDnqkNYWyUh1f4oK1  | pending until epoch xyz | NA              | ignore slot when calculating an account hash #28420
# 16FMCmgLzCNNz6eTwGanbyN2ZxvTBSLuQ6DZhgeMshg  | inactive                | NA              | Stop truncating strings in syscalls #31029
# 25vqsfjk7Nv1prsQJmA4Xu1bN61s8LXCBGUPp8Rfy1UF | inactive                | NA              | only hash accounts in incremental snapshot during incremental snapshot creation #26799'''
    most_recent_activated_pattern = re.compile(r'(.*active since epoch.*)')
    pending_pattern = re.compile(r'(.*pending until epoch.*)')
    activated_results = most_recent_activated_pattern.findall(status_text)
    pending_results = pending_pattern.findall(status_text)
    # print(activated_results)
    # print(pending_results)
    return activated_results[-3:] + pending_results
    
def get_next_feature_gates_by_cluster():
    return_value = {}
    url = "https://github.com/solana-labs/solana/wiki/Feature-Gate-Activation-Schedule.md"
    schedule_md = requests.get(url)

    pattern = re.compile(r"Current Schedule.*?Pending Mainnet Beta activation(?P<m>.*)Pending Devnet Activation(?P<d>.*)Pending Testnet Activation(?P<t>.*)Features are BLOCKED", flags=re.DOTALL)
    first_row = re.compile(r"-----.*?\n(.*?)\n", flags=re.DOTALL)
    matches = pattern.search(schedule_md.text)
    clusters = ['m', 'd', 't']
    for c in clusters:
        table = matches.group(c)
        row = first_row.search(table)
        parsed_row = parse_row(row.group(1))
        return_value[c] = parsed_row

    return return_value
    
def parse_row(row_md):
    pattern = re.compile(r"\|(?P<id>[^\|]*)\|(?P<version>[^\|]*)\|(?P<testnet>[^\|]*)\|(?P<devnet>[^\|]*)\|(?P<desc>[^\|]*)\|(?P<owner>[^\|]*)\|")
    desc_pattern = re.compile(r"\[(?P<desc>.*)\]\((?P<link>.*)?\)")
    parsed_row = pattern.search(row_md)
    if parsed_row is None:
        return None
    description = parsed_row.group('desc')
    parsed_desc = desc_pattern.search(description)

    result = FeatureGate(parsed_row.group('id').strip()
                         ,parsed_row.group('version').strip()
                         ,parsed_row.group('testnet').strip()
                         ,parsed_row.group('devnet').strip()
                         ,parsed_desc.group('desc').strip()
                         ,parsed_desc.group('link').strip()
                         ,parsed_row.group('owner').strip())
    return result