#########################################################
#
#  Main file for parallel mesh testing.
#
#  This is a modification of the run_parallel_advection.py
# file.
#
#
#  Authors: Linda Stals, Steve Roberts and Matthew Hardy,
# June 2005
#
#
#
#########################################################

import time
import sys
import numpy


#----------------------------
# Sequential interface
#---------------------------
from anuga import Transmissive_boundary, Reflective_boundary
from anuga import rectangular_cross_domain

#----------------------------
# Parallel interface
#---------------------------
from anuga_parallel.sequential_distribute import sequential_distribute_dump


t0 = time.time()

verbose = True

#--------------------------------------------------------------------------
# Setup functions for topograpy etc
#--------------------------------------------------------------------------
scale_me=1.0

def topography(x,y):
	return (-x/2.0 +0.05*numpy.sin((x+y)*200.0))*scale_me

def stagefun(x,y):
    stge=-0.2*scale_me #+0.01*(x>0.9)
    #topo=topography(x,y)
    return stge#*(stge>topo) + (topo)*(stge<=topo)


#--------------------------------------------------------------------------
# Setup Domain only on processor 0
#--------------------------------------------------------------------------
myid = 0
numprocs = 4



length = 2.0
width = 2.0
dx = dy = 0.005  # 640,000
dx = dy  = 0.05
domain = rectangular_cross_domain(int(length/dx), int(width/dy),
                                          len1=length, len2=width, verbose=verbose)


print domain.number_of_global_triangles

domain.set_store(True)
domain.set_flow_algorithm('tsunami')
domain.set_minimum_allowed_height(0.01)
domain.set_quantity('elevation',topography)     # Use function for elevation
domain.get_quantity('elevation').smooth_vertex_values()
domain.set_quantity('friction',0.03)            # Constant friction
domain.set_quantity('stage', stagefun)          # Constant negative initial stage
domain.get_quantity('stage').smooth_vertex_values()

domain.set_name('sw_rectangle')
#domain.print_statistics()


t1 = time.time()

if myid == 0 :
    print 'Create sequential domain ',t1-t0

if myid == 0 and verbose: 
    print 'DISTRIBUTING DOMAIN'
    sys.stdout.flush()
    
#barrier()

#-------------------------------------------------------------------------
# Distribute domain
#----------------------------------------------------------------------
#domain = distribute(domain,verbose=verbose)

sequential_distribute_dump(domain, numprocs, verbose = True)


t2 = time.time()

if myid == 0 :
    print 'Distribute domain ',t2-t1
    



