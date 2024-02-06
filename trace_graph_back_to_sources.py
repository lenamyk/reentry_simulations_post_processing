#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 11 18:25:57 2022

This script takes an activation wave (for example a reentrant wave) and traces the activation back to its sources with a resolution of 10 ms. Each source (initiation site) is defined as a cluster of 1000 nodes activated before its neighbouring nodes.

Inputs:
* elem_infile: Mesh element file for the ventricular model. Format is adapted from openCARPs .elem files, but without element type speficier and element tag.
* act_infile: Consists of activation times to consider, sorted from earliest to latest.

Steps:
Create initial graph of nodes with reentry activation times.
Create subgraph of nodes activated before threshold for each loop.
Activation cluster nodes are saved for each iteration.
If no components, read in relevant cluster from file and save or write to reentry list.

@author: lenamyklebust
"""
import numpy as np
import networkx as nx
from os.path import abspath
from argparse import ArgumentParser
from itertools import zip_longest
import pandas as pd
import csv


def flatlist(listtoflatten):
    return [item for sublist in listtoflatten for item in sublist]


def read_elems(filename):
    """
    Read in mesh elements from file.
    Each line consists of nodes defining an element.
    """
    elems = []
    with open(filename, "r") as filehandle:
        filecontents = filehandle.readlines()[
            1:
        ]  # Skips first line, since its empty in .onlynodes.elem
        for line in filecontents:
            current_line = line[:-1]
            current_line = current_line.split(" ")
            if len(current_line) == 4:  # Elem has 4 nodenrs
                elems.append(np.array(current_line).astype(int))
    return elems


def main(args):
    inpath = abspath(args.elem_infile)
    elems = read_elems(inpath)
    G = nx.Graph(flatlist([zip(e, np.roll(e, 1)) for e in elems]))
    del elems

    nodes_with_acttimes = np.array(pd.read_csv(args.act_infile, delimiter=" "))
    nodes_with_times_dict = {int(x): y for x, y in nodes_with_acttimes}
    nx.set_node_attributes(G, nodes_with_times_dict, name="act_time")

    min_time = np.min(nodes_with_acttimes[:, 1])
    early_reentry_time = nodes_with_acttimes[100000, 1]  # Pick the 100001nd activated node, to make sure you have properly started the reentry
    max_time = np.max(nodes_with_acttimes[:, 1])
        
    step = 10  # ms
    timethresholds_array = np.arange(min_time, max_time, step, dtype=int)
    del nodes_with_acttimes
    del nodes_with_times_dict

    # First reduction:
    nodes = (
        node
        for node, data in G.nodes(
            data=True
        )
        if data.get("act_time") and data.get("act_time") < timethresholds_array[-1]
    )
    G = G.subgraph(nodes)
    
    outcomp = []
    components = nx.connected_components(G)
    large_comp = [
        s for s in components if len(s) > 1000
    ]
    if len(large_comp) > 0:
        print("Component lengths > 1000:", [len(s) for s in large_comp])
        outcomp.extend(list(large_comp))
    if len(large_comp) > 1:
        print("Multiple reentries:", len(large_comp))

    with open(
        f"{args.outfile}_{timethresholds_array[-1]}", "w", newline=""
    ) as f:  # Assume large components in first iteration. This must be checked before running this script.
        outcomp = list(zip_longest(*outcomp))
        comp_head = np.array(range(len(large_comp)))
        np.savetxt(f, comp_head, fmt="%s", newline=" ")
        f.write('\n')
        writer = csv.writer(f, delimiter=" ")
        writer.writerows(outcomp)

    
    for time_threshold in reversed(timethresholds_array[:-1]):
            outcomp = []
            prev_threshold = time_threshold + step
            nr_of_cols = np.genfromtxt(f"{args.outfile}_{prev_threshold}", max_rows=1, dtype='str').size
    
            new_G_nodes = []
            header_all = []
            for colno in range(nr_of_cols):
                comp_pd = pd.read_csv(
                        f"{args.outfile}_{prev_threshold}", delimiter=" ", usecols=[colno]
                    ).dropna()
                header = str(comp_pd.columns.values[0])
                comp = np.array(comp_pd, dtype=int).flatten()
                nodes = [
                    node for node in comp if G.nodes[node].get("act_time") < time_threshold
                ]  # Choose nodes from large component with activation times below threshold
                                
                if (
                    len(nodes) < 1000
                ):  # If number of nodes < threhsold are too few, set column from previous iteration as a final (reduced) activation cluster
                    with open(f"{args.outfile}_reduced", "a", newline="") as f:
                        np.savetxt(f, ["Comp"], fmt="%s", newline="\n")
                        np.savetxt(f, comp, fmt="%s", newline="\n")
                    with open(f"{args.outfile}_meta", "a", newline="") as f:
                        np.savetxt(f, [f"Activation {header} of size {len(comp)} appears in {prev_threshold}"], fmt="%s", newline="\n")
                    continue
    
                subG = G.subgraph(
                    nodes
                )
                components = nx.connected_components(subG)
                large_comp = [s for s in components if len(s) > 1000]
                if (
                    len(large_comp) > 0
                ):  # If large components, write to node file for current threshold
                    print("Component lengths > 1000:", [len(s) for s in large_comp], f"time: {time_threshold}" )
                    outcomp.extend(list(large_comp))
                else:  # If no large comp for this cluster, set activation column from previous iteration as a final (reduced) activation cluster
                    with open(f"{args.outfile}_reduced", "a", newline="") as f:
                        np.savetxt(f, ["Comp"], fmt="%s", newline="\n")
                        np.savetxt(f, comp, fmt="%s", newline="\n")
                    with open(f"{args.outfile}_meta", "a", newline="") as f:
                        np.savetxt(f, [f"Activation {header} of size {len(comp)} appears in {prev_threshold}"], fmt="%s", newline="\n")
                    continue
                if len(large_comp) > 1:
                    print("Multiple reentries:", len(large_comp))
                    split_comp_header = [f"{header}.{c}" for c in np.arange(len(large_comp))]
                    header_all.extend(split_comp_header)
                    with open(f"{args.outfile}_meta", "a", newline="") as f:
                        savetext = [f"Last appearance at {time_threshold} before merge of activation wave {split_comp_header[n]} of size {len(large_comp[n])}" for n in range(len(large_comp))]
                        np.savetxt(f, savetext, fmt="%s", newline="\n")
                elif len(large_comp) == 1:
                    header_all.append(header)
                new_G_nodes.extend(nodes)
    
            if len(outcomp) > 0:
                with open(
                    f"{args.outfile}_{time_threshold}", "w", newline=""
                ) as f:
                    np.savetxt(f, header_all, fmt='%s', newline = ' ')    # Header with comp number from inputfile
                    f.write('\n')
                    outcomp = list(zip_longest(*outcomp))
                    writer = csv.writer(f, delimiter=" ")
                    writer.writerows(outcomp)
            else:
                break
    

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-e", "--elem_infile", required=True, type=str, help="Name of mesh element file"
    )
    parser.add_argument(
        "-a", "--act_infile", required=True, type=str, help="Name of activation file with relevant activations"
    )
    parser.add_argument(
        "-o", "--outfile", required=True, type=str, help="Name of output file"
    )
    args = parser.parse_args()
    main(args)
