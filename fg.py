from datetime import datetime, timedelta, timezone
import re
import requests
import subprocess
from typing import NamedTuple
import unittest
# from datetime import timedelta

def main():
    #  solana epoch-info -ut
    cluster_names = {'m': 'mainnet-beta', 't': 'testnet', 'd': 'devnet'}
    clusters = ['m', 'd', 't']
    # clusters = ['m', 't']
    pattern = re.compile(r'Epoch: (\d*)\\n.*Epoch Completed Time: [^/]*\/([^\(]*) \((.*) remaining\)')
    next_in_schedule = get_next_feature_gates_by_cluster()
    # print(next_in_schedule)


    # pattern = re.compile(r'Epoch: (\d*)\\n.*Epoch')
    parse_time_string("1day 18m 6s")
    for cluster in clusters: 
        epoch_info = subprocess.run(['solana', 'epoch-info', '-u'+ cluster], stdout=subprocess.PIPE)
        # print(str(epoch_info.stdout))
        match_result = pattern.search(str(epoch_info.stdout))
        # print(match_result.group(1))
        current_epoch = int(match_result.group(1))
        print("Cluster: " + cluster)
        print("Current epoch: " + str(current_epoch))
        print("Epoch length: " + match_result.group(2))
        epoch_duration = parse_time_string(match_result.group(2))
        print("Remaining: " + match_result.group(3))
        time_remaining = parse_time_string(match_result.group(3))
        print('\n'.join(get_recent_and_pending(cluster)))
        # next_boundary = datetime.now(timezone.utc) + time_remaining
        # print(next_boundary)
        # for i in range(0,3):
        #     next_boundary = next_boundary + epoch_length
        #     print("UTC: {}     Local time {}".format(next_boundary, next_boundary.astimezone().isoformat()))
        epochs = get_next_n_epoch_starts(current_epoch, time_remaining, epoch_duration, 3)
        for e in epochs:
            # print(e[1])
            # print("{} - {} - {} ".format(e[0], e[1].strftime("%a %m/%d, %H:%M"), e[1].astimezone().strftime("%a %m/%d, %H:%M")))
            print("{} - {} UTC".format(e[0], e[1].strftime("%a %m/%d, %H:%M")))
        fg = next_in_schedule[cluster]
        print("""
Thread Name: 
{key} - {desc}
First Message:
`{key} - {desc}` is next up for activation on {cluster}
{link}

Epoch {epoch} starts in {time_delta}

Any objection to this feature gate being activated?

cc: {owner}
""".format(key=fg.id
           ,desc=fg.desc
           ,cluster=cluster_names[cluster]
           ,link=fg.issue_link
           ,owner=fg.owner
           ,epoch=epochs[0][0]
           ,time_delta=time_remaining))
        print("-------------------------------------------------")

# TODO the time delta needs work. and expand {cluster}

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
    
class FgTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_parse_time_string(self):
        self.assertEqual(parse_time_string("17h 39m 23s"), timedelta(days=0, hours=17, minutes=39, seconds=23))
        self.assertEqual(parse_time_string("1day 10h 18m 6s"), timedelta(days=1, hours=10, minutes=18, seconds=6))
        self.assertEqual(parse_time_string("2days 10h 18m 6s"), timedelta(days=2, hours=10, minutes=18, seconds=6))
        self.assertEqual(parse_time_string("2days 5h 15m"), timedelta(days=2, hours=5, minutes=15, seconds=0))
        self.assertEqual(parse_time_string("2days 5h 6s"), timedelta(days=2, hours=5, minutes=0, seconds=6))
        self.assertEqual(parse_time_string("2days 5m 6s"), timedelta(days=2, hours=0, minutes=5, seconds=6))


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
        # print(parsed_row)
        return_value[c] = parsed_row

    return return_value
    
def parse_row(row_md):
    pattern = re.compile(r"\|(?P<id>[^\|]*)\|(?P<version>[^\|]*)\|(?P<testnet>[^\|]*)\|(?P<devnet>[^\|]*)\|(?P<desc>[^\|]*)\|(?P<owner>[^\|]*)\|")
    desc_pattern = re.compile(r"\[(?P<desc>.*)\]\((?P<link>.*)?\)")
    parsed_row = pattern.search(row_md)
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

class FeatureGate(NamedTuple):
    id: str
    version: str
    testnet: str
    devnet: str
    desc: str
    issue_link: str
    owner: str

main()
