from datetime import datetime, timedelta, timezone
import json
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

class SemVer(NamedTuple):
    major: int
    minor: int
    patch: int

schedule_md = None
schedule_json = None

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
# 6YsBCejwK96GZCkJ6mkZ4b68oP63z2PLoQmWjC7ggTqZ | pending until epoch 123                | NA              | consume duplicate proofs from blockstore in consensus #34372
# 16FMCmgLzCNNz6eTwGanbyN2ZxvTBSLuQ6DZhgeMshg  | inactive                | NA              | Stop truncating strings in syscalls #31029
# 25vqsfjk7Nv1prsQJmA4Xu1bN61s8LXCBGUPp8Rfy1UF | inactive                | NA              | only hash accounts in incremental snapshot during incremental snapshot creation #26799
# '''
    most_recent_activated_pattern = re.compile(r'(.*active since epoch.*)')
    pending_pattern = re.compile(r'(.*pending until epoch.*)')
    activated_results = most_recent_activated_pattern.findall(status_text)
    pending_results = pending_pattern.findall(status_text)
    # print(activated_results)
    # print(pending_results)
    return activated_results[-3:] + pending_results

# We only need this for version floors now. Those should be moved somewhere else in due course.
def get_schedule_md():
    global schedule_md
    if schedule_md is None:
        url = "https://github.com/anza-xyz/agave/wiki/Feature-Gate-Tracker-Schedule.md"
        print("Fetching: {}".format(url))
        schedule_md = requests.get(url)
    return schedule_md

def get_version_floor_by_cluster():
    return_value = {}
    schedule = get_schedule_md()
    find_row = re.compile(r"Version Floor.*Current floor([^\n]*)", flags=re.DOTALL)
    version_floor_row = find_row.search(schedule.text)
    # print(version_floor_row)
    parse_version_floor_row = re.compile(r"\|\s*(?P<t>[^\s\|]+)\s*\|\s*(?P<d>[^\s\|]+)\s*\|\s*(?P<m>[^\s\|]+)\s*")
    versions = parse_version_floor_row.search(version_floor_row.group(1))
    # print(versions)
    return_value['t'] = versions.group('t')
    return_value['d'] = versions.group('d')
    return_value['m'] = versions.group('m')
    # print(return_value)
    return return_value

def get_json_schedule():
    global schedule_json
    if schedule_json is None:
        url = "https://github.com/anza-xyz/agave/wiki/feature-gate-tracker-schedule.json"
        print("Fetching: {}".format(url))
        schedule_json = requests.get(url)
    schedule = json.loads(schedule_json.text)
    return schedule

def get_next_feature_gates_by_cluster():
    return_value = {}
    schedule = get_json_schedule()
    clusters = {'m': "1 - Ready for Mainnet-beta", 'd': "2 - Ready for Devnet", 't': "3 - Ready for Testnet"}
    for c in clusters:
        print("Checking FGs for cluster: {}".format(c))
        if clusters[c] not in schedule:
            # This cluster's schedule is empty
            print("Schedule is empty")
            return_value[c] = None
            continue

        fgs_for_this_cluster = schedule[clusters[c]]
        # This filter removes feature gates that haven't been explicitly scheduled. Usually unscheduled FGs don't make it
        # to the top of the queue, but this filter makes sure we don't activate one by accident.
        scheduled_fgs_for_this_cluster = list(filter(is_scheduled, fgs_for_this_cluster))

        if len(scheduled_fgs_for_this_cluster) == 0:
            print("Schedule is empty after filtering")
            return_value[c] = None
            continue

        sorted_fgs_for_this_cluster = sorted(scheduled_fgs_for_this_cluster, key=lambda fg: (fg["Testnet Epoch"], fg["Planned Testnet Order"]))
        return_value[c] = sorted_fgs_for_this_cluster[0]

    return return_value


def is_scheduled(fg):
    """
    Check if this FG is scheduled:
    - Testnet FGs require "Planned Testnet Order" to be populated
    - Devnet and mainnet-beta FGs require "Testnet Epoch" to be populated
    """
    if fg["Status"] == "3 - Ready for Testnet":
        return isinstance(fg["Planned Testnet Order"], int)
    else:
        return isinstance(fg["Testnet Epoch"], int)

#compare two semver
# version1  < version2 -> -1
# version1 == version2 ->  0
# version1  > version2 ->  1
def semver_compare(version1: SemVer, version2: SemVer):
    for v1, v2 in zip(version1, version2):
        if v1 < v2:
            return -1
        elif v2 < v1:
            return 1
    return 0

# Parse major.minor.patch from semver string. split on . and remove the V or v
def parse_semver(version):
    tokens = version.split(".")
    if len(tokens) != 3:
        raise ValueError("Error parsing semver: {}".format(version))
    try:
        return SemVer(int(tokens[0].replace("v", "").replace("V", "")), int(tokens[1]), int(tokens[2]))
    except:
        raise ValueError("Error parsing semver: {}".format(version))
