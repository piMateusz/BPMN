from more_itertools import pairwise
from collections import Counter
from itertools import chain
import pm4py
import pandas as pd


def load_df_from_file(file_path):
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    # since we accept only files with .xes and .csv extensions, we can use else here
    else:
        log = pm4py.read_xes(file_path)
        df = pm4py.convert_to_dataframe(log)

    return df


def load_from_file(file_path: str, case_id_col_name: str, timestamp_col_name: str, activity_col_name: str):
    df = load_df_from_file(file_path)
    df = df.rename(columns={case_id_col_name: "Case ID", timestamp_col_name: "Start Timestamp", activity_col_name: "Activity"})
    df = df[["Case ID", "Activity", "Start Timestamp"]]

    return df


def get_traces_from_df(df):
    dfs = (df
           .sort_values(by=['Case ID', 'Start Timestamp'])
           .groupby(['Case ID'])
           .agg({'Activity': ';'.join})
           )

    dfs['count'] = 0
    dfs = (
        dfs.groupby('Activity', as_index=False).count()
            .sort_values(['count'], ascending=False)
            .reset_index(drop=True)
    )

    dfs['trace'] = [trace.split(';') for trace in dfs['Activity']]
    return dfs


def get_ev_counter_from_df(df):
    return df.Activity.value_counts()


def create_w_net(dfs):
    w_net = dict()
    ev_start_set = set()
    ev_end_set = set()
    for index, row in dfs[['trace', 'count']].iterrows():
        if row['trace'][0] not in ev_start_set:
            ev_start_set.add(row['trace'][0])
        if row['trace'][-1] not in ev_end_set:
            ev_end_set.add(row['trace'][-1])
        for ev_i, ev_j in pairwise(row['trace']):
            if ev_i not in w_net.keys():
                w_net[ev_i] = Counter()
            w_net[ev_i][ev_j] += row['count']

    return w_net, ev_start_set, ev_end_set


def create_w_net_from_file(file_name, case_id_col_name, timestamp_col_name, activity_col_name):
    df = load_from_file(file_name, case_id_col_name, timestamp_col_name, activity_col_name)
    ev_counter = get_ev_counter_from_df(df)
    traces_df = get_traces_from_df(df)
    w_net, ev_start_set, ev_end_set = create_w_net(traces_df)
    trace_counts = sorted(chain(*[c.values() for c in w_net.values()]))
    trace_min = trace_counts[0]
    trace_max = trace_counts[-1]
    color_min = ev_counter.min()
    color_max = ev_counter.max()

    start_node_name = 'Start'
    end_node_name = 'End'

    ev_counter[start_node_name] = color_max + 1
    ev_counter[end_node_name] = color_max + 1

    w_net[start_node_name] = Counter()
    w_net[end_node_name] = Counter()

    for start_node in ev_start_set:
        w_net[start_node_name][start_node] = sum(w_net[start_node].values())
    for end_node in ev_end_set:
        if end_node not in w_net:
            w_net[end_node] = Counter()
        w_net[end_node][end_node_name] = sum(w_net[end_node].values())

    return ev_counter, trace_max, color_min, color_max, start_node_name, end_node_name, w_net, ev_start_set, ev_end_set