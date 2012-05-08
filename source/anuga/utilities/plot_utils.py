""" Random utilities for reading sww file data and for plotting (in ipython, or
    in scripts)

    Functionality of note:

    util.get_outputs -- read the data from a single sww file into a single object
    
    util.combine_outputs -- read the data from a list of sww files into a single object
    
    util.near_transect -- for finding the indices of points 'near' to a given
                       line, and assigning these points a coordinate along that line. 
                       This is useful for plotting outputs which are 'almost' along a
                       transect (e.g. a channel cross-section) -- see example below



    Here is an example ipython session which uses some of these functions:

    > import util
    > from matplotlib import pyplot as pyplot
    > p=util.get_output('myfile.sww',minimum_allowed_height=0.01)
    > p2=util.get_centroids(p,velocity_extrapolation=True)
    > xxx=util.near_transect(p,[95., 85.], [120.,68.],tol=2.) # Could equally well use p2
    > pyplot.ion() # Interactive plotting
    > pyplot.scatter(xxx[1],p.vel[140,xxx[0]],color='red') # Plot along the transect

"""
from Scientific.IO.NetCDF import NetCDFFile
import numpy

class combine_outputs:
    """
    Read in a list of filenames, and combine all their outputs into a single object.
    e.g.:

    p = util.combine_outputs(['file1.sww', 'file1_time_10000.sww', 'file1_time_20000.sww'], 0.01)
    
    will make an object p which has components p.x,p.y,p.time,p.stage, .... etc,
    where the values of stage / momentum / velocity from the sww files are concatenated as appropriate.

    This is nice for interactive interrogation of model outputs, or for sticking together outputs in scripts
   
    WARNING: It is easy to use lots of memory, if the sww files are large.

    Note: If you want the centroid values, then you could subsequently use:

    p2 = util.get_centroids(p,velocity_extrapolation=False)

    which would make an object p2 that is like p, but holds information at centroids
    """
    def __init__(self, filename_list, minimum_allowed_height=1.0e-03):
        #
        # Go through the sww files in 'filename_list', and combine them into one object.
        #

        for i, filename in enumerate(filename_list):
            print i, filename
            # Store output from filename
            p_tmp = get_output(filename, minimum_allowed_height)
            if(i==0):
                # Create self
                p1=p_tmp
            else:
                # Append extra data to self
                # Note that p1.x, p1.y, p1.vols, p1.elev should not change
                assert (p1.x == p_tmp.x).all()
                assert (p1.y == p_tmp.y).all()
                assert (p1.vols ==p_tmp.vols).all()
                p1.time = numpy.append(p1.time, p_tmp.time)
                p1.stage = numpy.append(p1.stage, p_tmp.stage, axis=0)
                p1.xmom = numpy.append(p1.xmom, p_tmp.xmom, axis=0)
                p1.ymom = numpy.append(p1.ymom, p_tmp.ymom, axis=0)
                p1.xvel = numpy.append(p1.xvel, p_tmp.xvel, axis=0)
                p1.yvel = numpy.append(p1.yvel, p_tmp.yvel, axis=0)
                p1.vel = numpy.append(p1.vel, p_tmp.vel, axis=0)

        self.x, self.y, self.time, self.vols, self.elev, self.stage, self.xmom, \
                self.ymom, self.xvel, self.yvel, self.vel, self.minimum_allowed_height = \
                p1.x, p1.y, p1.time, p1.vols, p1.elev, p1.stage, p1.xmom, p1.ymom, p1.xvel,\
                p1.yvel, p1.vel, p1.minimum_allowed_height



class get_output:
    """Read in data from an .sww file in a convenient form
       e.g. 
        p = util.get_output('channel3.sww', minimum_allowed_height=0.01)
        
       p then contains most relevant information as e.g., p.stage, p.elev, p.xmom, etc 
    """
    def __init__(self, filename, minimum_allowed_height=1.0e-03):
        self.x, self.y, self.time, self.vols, self.stage, \
                self.elev, self.xmom, self.ymom, \
                self.xvel, self.yvel, self.vel, self.minimum_allowed_height = \
                read_output(filename, minimum_allowed_height)


def read_output(filename, minimum_allowed_height):
    # Input: The name of an .sww file to read data from,
    #                    e.g. read_sww('channel3.sww')
    #
    # Purpose: To read the sww file, and output a number of variables as arrays that 
    #          we can then manipulate (e.g. plot, interrogate)
    #
    # Output: x, y, time, stage, elev, xmom, ymom, xvel, yvel, vel

    # Import modules



    # Open ncdf connection
    fid=NetCDFFile(filename)


    # Read variables
    x=fid.variables['x']
    x=x.getValue()
    y=fid.variables['y']
    y=y.getValue()

    stage=fid.variables['stage']
    stage=stage.getValue()

    elev=fid.variables['elevation']
    elev=elev.getValue()

    xmom=fid.variables['xmomentum']
    xmom=xmom.getValue()

    ymom=fid.variables['ymomentum']
    ymom=ymom.getValue()

    time=fid.variables['time']
    time=time.getValue()

    vols=fid.variables['volumes']
    vols=vols.getValue()


    # Calculate velocity = momentum/depth
    xvel=xmom*0.0
    yvel=ymom*0.0

    for i in range(xmom.shape[0]):
        xvel[i,:]=xmom[i,:]/(stage[i,:]-elev+1.0e-06)*(stage[i,:]> elev+minimum_allowed_height)
        yvel[i,:]=ymom[i,:]/(stage[i,:]-elev+1.0e-06)*(stage[i,:]> elev+minimum_allowed_height)

    vel = (xvel**2+yvel**2)**0.5

    return x, y, time, vols, stage, elev, xmom, ymom, xvel, yvel, vel, minimum_allowed_height

##############



class get_centroids:
    """
    Extract centroid values from the output of get_output.  
    e.g.
        p = util.get_output('my_sww.sww', minimum_allowed_height=0.01) # vertex values
        pc=util.get_centroids(p, velocity_extrapolation=True) # centroid values
    """
    def __init__(self,p, velocity_extrapolation=False):
        self.time, self.x, self.y, self.stage, self.xmom,\
             self.ymom, self.elev, self.xvel, \
             self.yvel, self.vel= \
             get_centroid_values(p, velocity_extrapolation)
                                 

def get_centroid_values(p, velocity_extrapolation):
    # Input: p is the result of e.g. p=util.get_output('mysww.sww'). See the get_output class defined above
    # Output: Values of x, y, Stage, xmom, ymom, elev, xvel, yvel, vel at centroids
    #import numpy
    
    # Make 3 arrays, each containing one index of a vertex of every triangle.
    l=len(p.vols)
    vols0=numpy.zeros(l, dtype='int')
    vols1=numpy.zeros(l, dtype='int')
    vols2=numpy.zeros(l, dtype='int')

    # FIXME: 22/2/12/ - I think this loop is slow, should be able to do this
    # another way
    for i in range(l):
        vols0[i]=p.vols[i][0]
        vols1[i]=p.vols[i][1]
        vols2[i]=p.vols[i][2]

    # Then use these to compute centroid averages 
    x_cent=(p.x[vols0]+p.x[vols1]+p.x[vols2])/3.0
    y_cent=(p.y[vols0]+p.y[vols1]+p.y[vols2])/3.0

    stage_cent=(p.stage[:,vols0]+p.stage[:,vols1]+p.stage[:,vols2])/3.0
    elev_cent=(p.elev[vols0]+p.elev[vols1]+p.elev[vols2])/3.0

    # Here, we need to treat differently the case of momentum extrapolation or
    # velocity extrapolation
    if velocity_extrapolation:
        xvel_cent=(p.xvel[:,vols0]+p.xvel[:,vols1]+p.xvel[:,vols2])/3.0
        yvel_cent=(p.yvel[:,vols0]+p.yvel[:,vols1]+p.yvel[:,vols2])/3.0
        
        # Now compute momenta
        xmom_cent=stage_cent*0.0
        ymom_cent=stage_cent*0.0

        t=len(p.time)

        for i in range(t):
            xmom_cent[i,:]=xvel_cent[i,:]*(stage_cent[i,:]-elev_cent+1.0e-06)*\
                                            (stage_cent[i,:]>elev_cent+p.minimum_allowed_height)
            ymom_cent[i,:]=yvel_cent[i,:]*(stage_cent[i,:]-elev_cent+1.0e-06)*\
                                            (stage_cent[i,:]>elev_cent+p.minimum_allowed_height)

    else:
        xmom_cent=(p.xmom[:,vols0]+p.xmom[:,vols1]+p.xmom[:,vols2])/3.0
        ymom_cent=(p.ymom[:,vols0]+p.ymom[:,vols1]+p.ymom[:,vols2])/3.0

        # Now compute velocities
        xvel_cent=stage_cent*0.0
        yvel_cent=stage_cent*0.0

        t=len(p.time)

        for i in range(t):
            xvel_cent[i,:]=xmom_cent[i,:]/(stage_cent[i,:]-elev_cent+1.0e-06)*(stage_cent[i,:]>elev_cent+p.minimum_allowed_height)
            yvel_cent[i,:]=ymom_cent[i,:]/(stage_cent[i,:]-elev_cent+1.0e-06)*(stage_cent[i,:]>elev_cent+p.minimum_allowed_height)
   

    # Compute velocity 
    vel_cent=(xvel_cent**2 + yvel_cent**2)**0.5

    return p.time, x_cent, y_cent, stage_cent, xmom_cent,\
             ymom_cent, elev_cent, xvel_cent, yvel_cent, vel_cent

# Make plot of stage over time.
#pylab.close()
#pylab.ion()
#pylab.plot(time, stage[:,1])
#for i in range(201):
#    pylab.plot(time,stage[:,i])

# Momentum should be 0. 
#print 'Momentum max/min is', xmom.max() , xmom.min()

#pylab.gca().set_aspect('equal')
#pylab.scatter(x,y,c=elev,edgecolors='none')
#pylab.colorbar()
#
#n=xvel.shape[0]-1
#pylab.quiver(x,y,xvel[n,:],yvel[n,:])
#pylab.savefig('Plot1.png')

def animate_1D(time, var, x, ylab=' '): #, x=range(var.shape[1]), vmin=var.min(), vmax=var.max()):
    # Input: time = one-dimensional time vector;
    #        var =  array with first dimension = len(time) ;
    #        x = (optional) vector width dimension equal to var.shape[1];
    
    import pylab
    import numpy
   
    

    pylab.close()
    pylab.ion()

    # Initial plot
    vmin=var.min()
    vmax=var.max()
    line, = pylab.plot( (x.min(), x.max()), (vmin, vmax), 'o')

    # Lots of plots
    for i in range(len(time)):
        line.set_xdata(x)
        line.set_ydata(var[i,:])
        pylab.draw()
        pylab.xlabel('x')
        pylab.ylabel(ylab)
        pylab.title('time = ' + str(time[i]))
    
    return

def near_transect(p, point1, point2, tol=1.):
    # Function to get the indices of points in p less than 'tol' from the line
    # joining (x1,y1), and (x2,y2)
    # p comes from util.get_output('mysww.sww')
    #
    # e.g.
    # import util
    # from matplotlib import pyplot
    # p=util.get_output('merewether_1m.sww',0.01)
    # p2=util.get_centroids(p,velocity_extrapolation=True)
    # #xxx=transect_interpolate.near_transect(p,[95., 85.], [120.,68.],tol=2.)
    # xxx=util.near_transect(p,[95., 85.], [120.,68.],tol=2.)
    # pyplot.scatter(xxx[1],p.vel[140,xxx[0]],color='red')

    x1=point1[0]
    y1=point1[1]

    x2=point2[0]
    y2=point2[1]

    # Find line equation a*x + b*y + c = 0
    # based on y=gradient*x +intercept
    if x1!=x2:
        gradient= (y2-y1)/(x2-x1)
        intercept = y1 - gradient*x1

        a = -gradient
        b = 1.
        c = -intercept
    else:
        #print 'FIXME: Still need to treat 0 and infinite gradients'
        #assert 0==1
        a=1.
        b=0.
        c=-x2 

    # Distance formula
    inv_denom = 1./(a**2 + b**2)**0.5
    distp = abs(p.x*a + p.y*b + c)*inv_denom

    near_points = (distp<tol).nonzero()[0]
    
    # Now find a 'local' coordinate for the point, projected onto the line
    # g1 = unit vector parallel to the line
    # g2 = vector joining (x1,y1) and (p.x,p.y)
    g1x = x2-x1 
    g1y = y2-y1
    g1_norm = (g1x**2 + g1y**2)**0.5
    g1x=g1x/g1_norm
    g1y=g1x/g1_norm

    g2x = p.x[near_points] - x1
    g2y = p.y[near_points] - y1
    
    # Dot product = projected distance == a local coordinate
    local_coord = g1x*g2x + g1y*g2y

    return near_points, local_coord