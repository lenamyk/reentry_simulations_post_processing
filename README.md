# reentry_simulations_post_processing


This folder contains scripts for post processing reentrant activity.



## trace_graph_back_to_sources.py
This script traces the reentrant wave back to its sources with a resolution of 10 ms. Each source (initiation site) is defined as a cluster of 1000 nodes activated before its neighbouring nodes.
Inputs:
* elem_infile: Mesh element file for the ventricular model. Format is adapted from openCARPs .elem files, but without element type speficier and element tag. Instead, only the vertices for each element are listed per line.

  Example:
  
  917393 917441 917618 917498
  
  516035 516065 517204 516086 

  281890 282157 281912 282177
  
  ...
  
  Where each line defines an element consisting of four vertices.

* 


Usage:
python3.9 trace_graph_back_to_sources.py -e element_file_onlynodes.elem  -a reentry_nodes_with_activation_times_sorted -o reentry_clusters
