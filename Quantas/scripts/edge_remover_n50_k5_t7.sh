#!/bin/bash

#OAR -n edge_remover_n50_k5_t7
#OAR -l { host in ('big16','big17','big18', 'big19', 'big20', 'tall1', 'tall2', 'tall3', 'tall4', 'tall5', 'tall6', 'tall7', 'tall8', 'tall9', 'tall10', 'tall11', 'tall12', 'tall13', 'tall14', 'tall15', 'tall16', 'tall17', 'tall18', 'tall19', 'tall20')}/nodes=1/core=48,walltime=1000:0:0
#OAR -O server_output/edge_remover_n50_k5_t7.stdout
#OAR -E server_output/edge_remover_n50_k5_t7.stderr

source /etc/profile.d/modules.sh                # Shell initialization to use module
make run INPUTFILE=quantas/topologies/edge_remover_n50_k5_t7.json