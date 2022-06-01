from typing import Dict, Set
from collections import defaultdict, Counter
from itertools import combinations
import copy


def get_causality(direct_succession) -> Dict[str, Set[str]]:
    causality = defaultdict(set)
    for ev_cause, events in direct_succession.items():
        for event in events:
            if ev_cause not in direct_succession.get(event, set()):
                causality[ev_cause].add(event)
    return dict(causality)


def get_inv_causality(causality) -> Dict[str, Set[str]]:
    inv_causality = defaultdict(set)
    for key, values in causality.items():
        for value in values:
            inv_causality[value].add(key)
    return {k: v for k, v in inv_causality.items() if len(v) > 1}


def get_parrallel(direct_succesion):
    parrarel_events = set()
    for event, successors in direct_succesion.items():
        for succesor in successors:
            if succesor in direct_succesion:
                if event in direct_succesion[succesor]:
                    parrarel_events.add(tuple(sorted([event, succesor])))
    return parrarel_events


def sort_graph_dict(graph_dict, ev_counter):
    # sort nodes asc
    sorted_nodes = dict(sorted(graph_dict.items(), key=lambda x:ev_counter[x[0]], reverse=False))
    # sort edges asc
    sorted_dict = {event: dict(sorted(successors.items(), key=lambda x:x[1], reverse=False)) for event, successors in sorted_nodes.items()}
    return sorted_dict


def dfs(visited, graph, node):
    if node not in visited:
        visited.add(node)
        for neighbour in graph[node]:
            dfs(visited, graph, neighbour)


def check_graph_coherence(graph_dict, start_node_name, end_node_name, node_to_delete=None, node_predecessor=None, node_successor=None):
    """
    Method for checking with dfs algorithm if end node is reachable after deleting selected node or edge
    :param graph_dict: dictionary describing graph connections
    :param node_to_delete: node that is below threshold and could be possibly deleted
    :param node_predecessor: node that is the beginning of the edge that is below threshold and could be possibly deleted
    :param node_successor: node that is the end of the edge that is below threshold and could be possibly deleted
    :return: graph dict with deleted node or edge if graph is still coherent, else unchanged dict
    """
    visited = set()
    temp_dict = copy.deepcopy(graph_dict)
    if node_to_delete is not None:
        # delete node key from dict
        temp_dict.pop(node_to_delete, None)
        temp_dict_2 = copy.deepcopy(temp_dict)
        for event, successors in temp_dict.items():
            for successor, cnt in successors.items():
                if successor == node_to_delete:
                    temp_dict_2[event].pop(node_to_delete, None)
        temp_dict = copy.deepcopy(temp_dict_2)
    if node_predecessor is not None:
        # delete edge between node_predecessor and node_successor from dict
        temp_dict[node_predecessor].pop(node_successor, None)
    dfs(visited, temp_dict, start_node_name)
    if end_node_name in visited:
        return temp_dict
    else:
        return graph_dict


def check_no_direct_succession(successors, direct_succession):
    no_direct_successors = set()
    successors_combinations = combinations(successors, 2)
    for first_successor, second_successor in successors_combinations:
        if second_successor not in direct_succession[first_successor] and first_successor not in direct_succession[second_successor]:
            no_direct_successors.add(first_successor)
            no_direct_successors.add(second_successor)
    return no_direct_successors


def find_node_successors_and_predecessors(graph_dict, node):
    """
    :return: node successors (Counter objec) and predecessors (list)
    """
    node_successors = Counter()
    node_predecessors = []
    for event, succesors in graph_dict.items():
        if event == node:
            if succesors:
                node_successors = succesors
        for succesor, cnt in succesors.items():
            if succesor == node:
                node_predecessors.append(event)
    return node_predecessors, node_successors


def delete_unconnected_nodes(graph_dict, start_node_name, end_node_name):
    """
    Delete not fully connected nodes and edges that are not in 'main path'
    :return: changed graph dictionary
    """
    temp_dict = copy.deepcopy(graph_dict)
    is_unconnected_node = True
    while is_unconnected_node:
        is_unconnected_node = False
        for event, succesors in graph_dict.items():
            # omit start and end event in checking connections - these nodes have only inputs or outputs
            if event in [start_node_name, end_node_name]:
                continue
            node_predecessors, node_successors = find_node_successors_and_predecessors(temp_dict, event)
            if not node_predecessors or not node_successors:
                is_unconnected_node = True
                # node doesn't have either any predecessors or successors
                # delete node (therefore node -> successors edges)
                temp_dict.pop(event, None)
                # delete predecessors -> node edges
                for node_predecessor in node_predecessors:
                    temp_dict[node_predecessor].pop(event, None)
                graph_dict = copy.deepcopy(temp_dict)
                break
    return temp_dict


def alpha_algorithm(direct_connections):
    causalities = get_causality(direct_connections)  # a -> b
    inv_causalities = get_inv_causality(causalities)
    potential_parallelism = get_parrallel(direct_connections)  # a || b
    split_xor_gates = {}
    join_xor_gates = {}

    # XOR gates
    # 4b - split XOR gates
    for predecessor, successors in causalities.items():
        if len(successors) > 1:
            xor_split_successors = check_no_direct_succession(successors, direct_connections)
            if xor_split_successors:
                split_xor_gates[predecessor] = xor_split_successors

    # 4c - join XOR gates
    for sucessor, predecessors in inv_causalities.items():
        if len(predecessors) > 1:
            xor_join_predecessors = check_no_direct_succession(predecessors, direct_connections)
            if xor_join_predecessors:
                join_xor_gates[sucessor] = xor_join_predecessors

    # Eliminacja causalities z bram z 4b
    for predecessor, successors in split_xor_gates.items():
        for successor in successors:
            if successor in causalities[predecessor]:
                causalities[predecessor].remove(successor)

    # Eliminacja causalities z bram z 4c
    for successor, predecessors in join_xor_gates.items():
        for predecessor in predecessors:
            if successor in causalities[predecessor]:
                causalities[predecessor].remove(successor)

    inv_causalities = get_inv_causality(causalities)
    return causalities, inv_causalities, potential_parallelism, split_xor_gates, join_xor_gates
