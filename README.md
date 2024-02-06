# reentry_simulations_post_processing


This folder contains scripts for post processing simulated activity.



## trace_graph_back_to_sources.py
This script traces the activation back to its sources with a resolution of 10 ms. Each source (initiation site) is defined as a cluster of 1000 nodes activated before its neighbouring nodes. The script is used to find initiation sites for reentry, given that the activations caused by the reentrant wave has been identified.
Inputs:
* elem_infile: Mesh element file for the ventricular model. Format is adapted from openCARPs .elem files, but without element type speficier and element tag. 

  Example:\
  917393 917441 917618 917498 \
  516035 516065 517204 516086 \
  281890 282157 281912 282177 \
  ... \
  
  Where each line defines an element consisting of four vertices.

* act_infile: Consists of activation times to consider (for example a reentrant wave), sorted from earliest to latest. 

  Example:\
  220507 1879.918604 \
  218470 1880.632104 \
  231275 1881.603445 \
  ... \

  Where the first column is the vertex number and the second is the corresponding activation times.

Usage:
python3.9 trace_graph_back_to_sources.py -e element_file_onlynodes.elem  -a reentry_nodes_with_activation_times_sorted -o source_clusters

Outputs:
*  source_clusters_timepoint: Activation clusters at each time point 
*  source_clusters_reduced: Final activation clusters, defining the sources of activation
*  source_clusters_meta: Information about when each cluster of activation appears. If multiple initiation sites, this file also specifies when these activation waves merge together

