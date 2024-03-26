### TODO
# compare cluster min versions against the next few fg versions
# parallelize

from datetime import datetime, timedelta, timezone
import re
import requests
import subprocess
from typing import NamedTuple
import unittest
from fg_lib import *

def main():
    cluster_names = {'m': 'mainnet-beta', 't': 'testnet', 'd': 'devnet'}
    clusters = ['m', 'd', 't']
    pattern = re.compile(r'Epoch: (\d*)\\n.*Epoch Completed Time: [^/]*\/([^\(]*) \((.*) remaining\)')
    next_in_schedule = get_next_feature_gates_by_cluster()
    # print(next_in_schedule)
    version_floors = get_version_floor_by_cluster()
    print("Version floors: {}".format(version_floors))

    print("-----------------------------------------------------------")
    for cluster in clusters: 
        epoch_info = subprocess.run(['solana', 'epoch-info', '-u'+ cluster], stdout=subprocess.PIPE)
        # print(str(epoch_info.stdout))
        match_result = pattern.search(str(epoch_info.stdout))
        # print(match_result.group(1))
        current_epoch = int(match_result.group(1))
        print("Cluster: " + cluster_names[cluster])
        print("Current epoch: " + str(current_epoch))
        print("Version floor: " + version_floors[cluster])
        print("Epoch length: " + match_result.group(2))
        epoch_duration = parse_time_string(match_result.group(2))
        print("Remaining: " + match_result.group(3))
        time_remaining = parse_time_string(match_result.group(3))
        recent_and_pending_activations = get_recent_and_pending(cluster)
        print('\n'.join(recent_and_pending_activations))
        epochs = get_next_n_epoch_starts(current_epoch, time_remaining, epoch_duration, 5)
        for e in epochs:
            print("{} - {} UTC".format(e[0], e[1].strftime("%a %m/%d, %H:%M")))
        fg = next_in_schedule[cluster]
        parsed_fg_version = parse_semver(fg.version)
        parsed_cluster_version_floor = parse_semver(version_floors[cluster])
        version_floor_needs_to_be_raised = semver_compare(parsed_fg_version, parsed_cluster_version_floor) > 0

        print("parsed_fg_version: {}".format(parsed_fg_version))
        print("parsed_cluster_version_floor: {}".format(parsed_cluster_version_floor))
        print("version_floor_needs_to_be_raised: {}".format(version_floor_needs_to_be_raised))

        if fg is None:
            print("No feature gates scheduled for {cluster}\n".format(cluster=cluster_names[cluster]))
        elif any(fg.id in activated_feature for activated_feature in recent_and_pending_activations):
            print("""Top feature gate on the schedule is {key} - {desc}. It has already been activated. Update the wiki and re-run.\n"""
                  .format(key=fg.id, desc=fg.desc))
        elif version_floor_needs_to_be_raised:
            print("""Top feature gate on the schedule is {key} - {desc}. It will raise the version floor from {cluster_version} to {fg_version}. Update the wiki version floor and re-run.\n"""
                   .format(key=fg.id, desc=fg.desc, cluster_version=version_floors[cluster], fg_version=fg.version))
        else:
            print("""
Thread Name: 
{key} - {desc}
First Message:
`{key} - {desc}` is next up for activation on {cluster}
{link}. It requires at least version {version}

Epoch {epoch} starts in {time_delta}

Any objection to this feature gate being activated?

cc: {owner}
""".format(key=fg.id
           ,desc=fg.desc
           ,cluster=cluster_names[cluster]
           ,link=fg.issue_link
           ,version=fg.version
           ,owner=fg.owner
           ,epoch=epochs[0][0]
           ,time_delta=time_remaining))
        print("-----------------------------------------------------------")


main()
