from django.conf import settings

from itertools import combinations
from datetime import datetime
import pygraphviz as pgv
import os
import copy

from .media_utils import delete_folder_contents
from .alpha_algorithm import sort_graph_dict, check_graph_coherence, delete_unconnected_nodes, alpha_algorithm
from .w_net import create_w_net_from_file


class MyGraph(pgv.AGraph):

    def __init__(self, *args):
        super(MyGraph, self).__init__(strict=False, directed=True, *args)
        self.graph_attr['rankdir'] = 'LR'
        self.node_attr['shape'] = 'Mrecord'
        self.graph_attr['splines'] = 'ortho'
        self.graph_attr['nodesep'] = '0.8'
        self.edge_attr.update(penwidth='2')

    def add_event(self, name):
        super(MyGraph, self).add_node(name, shape="circle", label="")

    def add_end_event(self, name):
        super(MyGraph, self).add_node(name, shape="circle", label="", penwidth='3')

    def add_and_gateway(self, *args):
        super(MyGraph, self).add_node(*args, shape="diamond",
                                      width=".7", height=".7",
                                      fixedsize="true",
                                      fontsize="40", label="+")

    def add_xor_gateway(self, *args, **kwargs):
        super(MyGraph, self).add_node(*args, shape="diamond",
                                      width=".7", height=".7",
                                      fixedsize="true",
                                      fontsize="40", label="×")

    def add_and_split_gateway(self, source, targets, *args):
        gateway = 'ANDs ' + str(source) + '->' + str(targets)
        self.add_and_gateway(gateway, *args)
        super(MyGraph, self).add_edge(source, gateway)
        for target in targets:
            super(MyGraph, self).add_edge(gateway, target)

    def add_xor_split_gateway(self, source, targets, *args):
        gateway = 'XORs ' + str(source) + '->' + str(targets)
        self.add_xor_gateway(gateway, *args)
        super(MyGraph, self).add_edge(source, gateway)
        for target in targets:
            super(MyGraph, self).add_edge(gateway, target)

    def add_and_merge_gateway(self, sources, target, *args):
        gateway = 'ANDm ' + str(sources) + '->' + str(target)
        self.add_and_gateway(gateway, *args)
        super(MyGraph, self).add_edge(gateway, target)
        for source in sources:
            super(MyGraph, self).add_edge(source, gateway)

    def add_xor_merge_gateway(self, sources, target, *args):
        gateway = 'XORm ' + str(sources) + '->' + str(target)
        self.add_xor_gateway(gateway, *args)
        super(MyGraph, self).add_edge(gateway, target)
        for source in sources:
            super(MyGraph, self).add_edge(source, gateway)


def create_graph(start_set_events, end_set_events, causalities, inv_causalities,
                 potential_parallelism, split_xor_gates, join_xor_gates,
                 start_event_name="start", end_event_name="end", enable_filtration=False, append=None):
    G = MyGraph()

    if not enable_filtration:
        # adding start event
        G.add_event(start_event_name)
        if len(start_set_events) > 1:
            if tuple(sorted(start_set_events)) in potential_parallelism:
                G.add_and_split_gateway(start_event_name, start_set_events)
            else:
                G.add_xor_split_gateway(start_event_name, start_set_events)
        else:
            G.add_edge(start_event_name, list(start_set_events)[0])

    # adding split gateways based on casuality

    # adding xor split gateways
    for source, targets in split_xor_gates.items():
        G.add_xor_split_gateway(source=source, targets=targets)

    # adding and split gateways
    for event in causalities:
        # adding and split gateways
        if len(causalities[event]) > 1:
            comb = combinations(causalities[event], 2)
            sorted_comb = {tuple(sorted(parrarel_pair)) for parrarel_pair in comb}
            if sorted_comb.issubset(potential_parallelism):
                G.add_and_split_gateway(event, causalities[event])

        # adding connection
        elif len(causalities[event]) == 1:
            target = list(causalities[event])[0]
            if target not in inv_causalities:
                G.add_edge(event, target)

    # adding merge gateways based on inverted causality

    # adding xor merge gateways
    for target, sources in join_xor_gates.items():
        G.add_xor_merge_gateway(sources=sources, target=target)

    for event in inv_causalities:
        # adding and merge gateways
        if len(inv_causalities[event]) > 1:
            comb = combinations(inv_causalities[event], 2)
            sorted_comb = {tuple(sorted(parrarel_pair)) for parrarel_pair in comb}
            if sorted_comb.issubset(potential_parallelism):
                G.add_and_merge_gateway(inv_causalities[event], event)

        # adding connection
        elif len(inv_causalities[event]) == 1:
            source = list(inv_causalities[event])[0]
            G.add_edge(source, event)

    if not enable_filtration:
        # adding end event
        G.add_end_event(end_event_name)
        if len(end_set_events) > 1:
            if tuple(sorted(end_set_events)) in potential_parallelism:
                G.add_and_merge_gateway(end_set_events, end_event_name)
            else:
                G.add_xor_merge_gateway(end_set_events, end_event_name)
        else:
            G.add_edge(list(end_set_events)[0], end_event_name)

    img_file_name = 'simple_process_model.png' if append is None else f"simple_process_model_{append}.png"
    img_folder = "images"
    img_folder_path = os.path.join(settings.MEDIA_ROOT, img_folder)

    # delete /media/images contents
    delete_folder_contents(img_folder_path)

    # save new graph image
    img_path = os.path.join(img_folder_path, img_file_name)
    G.draw(img_path, prog='dot')

    img_rel_path = os.path.join(settings.MEDIA_URL, img_folder, img_file_name)
    return img_rel_path


def display_bpmn_model(file_path, node_threshold, edge_threshold):
    # create bpmn_utils from file
    ev_counter, trace_max, color_min, color_max, start_node_name, end_node_name, \
    w_net, start_set_events, end_set_events = create_w_net_from_file(file_path)

    sorted_w_net = sort_graph_dict(w_net, ev_counter)
    basic_graph_dict = copy.deepcopy(sorted_w_net)

    # try to delete nodes
    for event, succesors in sorted_w_net.items():
        value = ev_counter[event]
        if node_threshold > value:
            basic_graph_dict = check_graph_coherence(basic_graph_dict, start_node_name, end_node_name,
                                                     node_to_delete=event)

    # try to delete edges
    for event, succesors in basic_graph_dict.items():
        for succesor, cnt in succesors.items():
            if edge_threshold > cnt:
                basic_graph_dict = check_graph_coherence(basic_graph_dict, start_node_name, end_node_name,
                                                         node_predecessor=event, node_successor=succesor)

    # check node connections and delete nodes and edges that aren't appropriately connected
    basic_graph_dict = delete_unconnected_nodes(basic_graph_dict, start_node_name, end_node_name)

    # perform alpha algorithm
    causalities, inv_causalities, potential_parallelism, split_xor_gates, join_xor_gates = alpha_algorithm(
        basic_graph_dict)

    img_src_appendix = str(datetime.timestamp(datetime.now()))
    img_src = create_graph(start_set_events, end_set_events, causalities, inv_causalities,
                           potential_parallelism, split_xor_gates, join_xor_gates,
                           start_event_name=start_node_name, end_event_name=end_node_name,
                           enable_filtration=True, append=img_src_appendix)

    return img_src, trace_max, color_max
