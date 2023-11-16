### TODO
# get the cluster min version
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
        epochs = get_next_n_epoch_starts(current_epoch, time_remaining, epoch_duration, 5)
        for e in epochs:
            # print(e[1])
            # print("{} - {} - {} ".format(e[0], e[1].strftime("%a %m/%d, %H:%M"), e[1].astimezone().strftime("%a %m/%d, %H:%M")))
            print("{} - {} UTC".format(e[0], e[1].strftime("%a %m/%d, %H:%M")))
        fg = next_in_schedule[cluster]
        if fg is None:
            print("No feature gate scheduled for {cluster}".format(cluster=cluster_names[cluster]))
        else:
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




main()


