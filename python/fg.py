### TODO
# compare cluster min versions against the next few fg versions
# parallelize
# TODO the output needs to show if a FG is blocked. This will require switching from the public json schedule to a private one, since we don't publish the blocked status.

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

        if fg is None:
            print("No feature gates scheduled for {cluster}\n".format(cluster=cluster_names[cluster]))
            print("-----------------------------------------------------------")

            continue

        # cluster:
        # 2.2.6

        # this:
        # 2.2.4, 2.1.21       OK
        # 2.2.7, 2.1.21       need to raise
        # cluster version floor should be:
        # client:
        #     list:

        # Your version must be >= any of the versions in the list
        # A FG raises the version floor by:
        #     match up lists by major.minor
        #         Remove any floor versions that don't have corresponding FG mins
        #         For all that match do floor = major.min.max(patch, patch)

# commenting until I get verison floors sorted out
        # parsed_fg_version = parse_semver(fg.version) # ",".join(fg["Min Agave Versions"])
        # parsed_cluster_version_floor = parse_semver(version_floors[cluster])
        # version_floor_needs_to_be_raised = semver_compare(parsed_fg_version, parsed_cluster_version_floor) > 0

        # print("parsed_fg_version: {}".format(parsed_fg_version))
        # print("parsed_cluster_version_floor: {}".format(parsed_cluster_version_floor))
        # print("version_floor_needs_to_be_raised: {}".format(version_floor_needs_to_be_raised))

        if any(fg["Feature ID"] in activated_feature for activated_feature in recent_and_pending_activations):
            print("""Top feature gate on the schedule is {key} - {desc}.
It has already been activated. Update the wiki and re-run.
https://github.com/anza-xyz/agave/wiki/Feature-Gate-Activation-Schedule"""
                  .format(key=fg["Feature ID"], desc=fg["Title"]))
#         elif version_floor_needs_to_be_raised:
#             print("""Top feature gate on the schedule is {key} - {desc}.
# It will raise the version floor from {cluster_version} to {fg_version}. Update the wiki version floor and re-run.
# https://github.com/anza-xyz/agave/wiki/Feature-Gate-Activation-Schedule"""
#                    .format(key=fg["Feature ID"], desc=fg["Title"], cluster_version=version_floors[cluster], fg_version=",".join(fg["Min Agave Versions"])))
        else:
            print("message for {key}".format(key=fg["Feature ID"]))

            print("""
Thread Name:
{key} - {desc}
First Message:
`{key} - {desc}` is next up for activation on {cluster}.
It requires at least Agave version {agave_version}

Epoch {epoch} starts in {time_delta}

Any objection to this feature gate being activated?

cc: {owner}
""".format(key=fg["Feature ID"]
           ,desc=fg["Title"]
           ,cluster=cluster_names[cluster]
        #    ,link=fg.issue_link
           # TODO other versions
           ,agave_version=",".join(fg["Min Agave Versions"])
           ,owner=",".join(fg["Owners"])
           ,epoch=epochs[0][0]
           ,time_delta=time_remaining))
        print("-----------------------------------------------------------")


main()
