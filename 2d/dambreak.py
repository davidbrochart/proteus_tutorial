"""
dambreak 2-D
"""
from proteus import (Domain, Context)
from proteus.mprans.SpatialTools import Tank2D
from proteus.mprans import SpatialTools as st
import proteus.TwoPhaseFlow.TwoPhaseFlowProblem as TpFlow
from proteus.Gauges import PointGauges, LineIntegralGauges, LineGauges
import numpy as np
# *************************** #
# ***** GENERAL OPTIONS ***** #
# *************************** #
opts= Context.Options([
    ("final_time",3.0,"Final time for simulation"),
    ("dt_output",0.01,"Time interval to output solution"),
    ("cfl",0.9,"Desired CFL restriction"),
    ("he",0.01,"he relative to Length of domain in x"),
    ("refinement",3,"level of refinement")
    ])

# ****************** #
# ***** GAUGES ***** #
# ****************** #
height_gauges1 = LineGauges(gauges=((("phi",),
                                     (((2.724, 0.0, 0.0),
                                       (2.724, 1.8, 0.0)), # We consider this one in our paper
                                      ((2.228, 0.0, 0.0),
                                       (2.228, 1.8, 0.0)), # We consider this one in our paper
                                      ((1.732, 0.0, 0.0),
                                       (1.732, 1.8, 0.0)),
                                      ((0.582, 0.0, 0.0),
	                               (0.582, 1.8, 0.0)))),),
                            fileName="height1.csv")

height_gauges2 = LineGauges(gauges=((("phi",),
                                     (((0.0, 0.0, 0.0),
                                       (0.0, 0.0, -0.01)),
                                      ((0.0, 0.0, 0.0),
                                       (3.22, 0.0, 0.0)))),),
                            fileName="height2.csv")

pressure_gauges = PointGauges(gauges=((('p',),
                                       ((3.22, 0.16, 0.0), #P1                                                               
                                        (3.22, 0.584, 0.0), #P3                                                               
                                        (3.22, 0.12, 0.0))),), # This is the one considered in our paper
                              fileName="pressure.csv")

# *************************** #
# ***** DOMAIN AND MESH ***** #
# ****************** #******* #
tank_dim = (3.22,1.8) 
refinement = opts.refinement
structured=False
if structured:
    nny = 5*(2**refinement)+1
    nnx = 2*(nnx-1)+1
    domain = Domain.RectangularDomain(tank_dim)
    boundaryTags = domain.boundaryTags
    triangleFlag=1
else:
    nnx = nny = None
    domain = Domain.PlanarStraightLineGraphDomain()

# ----- TANK ----- #
tank = Tank2D(domain, tank_dim) 

# ----- BOUNDARY CONDITIONS ----- #
tank.BC['y+'].setAtmosphere()
tank.BC['y-'].setFreeSlip()
tank.BC['x+'].setFreeSlip()
tank.BC['x-'].setFreeSlip()


#my_rectangle = st.Rectangle(domain, dim=[0.5, 0.2], coords=[2.5, 0.21])
#tank.setHoles([[2.6, 0.22]])    
#my_rectangle.holes_ind = np.array([0])

#my_rectangle.BC['y+'].setFreeSlip()
#my_rectangle.BC['y-'].setFreeSlip()
#my_rectangle.BC['x+'].setFreeSlip()
#my_rectangle.BC['x-'].setFreeSlip()

he = tank_dim[0]*opts.he
domain.MeshOptions.he = he
st.assembleDomain(domain)
domain.MeshOptions.triangleOptions = "VApq30Dena%8.8f" % ((he ** 2)/2.0,)

# ****************************** #
# ***** INITIAL CONDITIONS ***** #
# ****************************** #
class zero(object):
    def uOfXT(self,x,t):
        return 0.0

waterLine_y = 0.6
waterLine_x = 1.2
class VF_IC:
    def uOfXT(self, x, t):
        if x[0] < waterLine_x and x[1] < waterLine_y:
            return 0.0
        else:
            return 1.0

class PHI_IC:
    def uOfXT(self, x, t):
        phi_x = x[0] - waterLine_x
        phi_y = x[1] - waterLine_y
        if phi_x < 0.0:
            if phi_y < 0.0:
                return max(phi_x, phi_y)
            else:
                return phi_y
        else:
            if phi_y < 0.0:
                return phi_x
            else:
                return (phi_x ** 2 + phi_y ** 2)**0.5
        
############################################
# ***** Create myTwoPhaseFlowProblem ***** #
############################################
outputStepping = TpFlow.OutputStepping(opts.final_time,dt_output=opts.dt_output)
initialConditions = {'pressure': zero(),
                     'pressure_increment': zero(),
                     'vel_u': zero(),
                     'vel_v': zero(),
                     'vof': VF_IC(),
                     'ncls': PHI_IC(),
                     'rdls': PHI_IC()}

auxVariables={'ncls': [height_gauges1, height_gauges2],
              'pressure': [pressure_gauges]}

myTpFlowProblem = TpFlow.TwoPhaseFlowProblem(ns_model=0,
                                             ls_model=0,
                                             nd=2,
                                             cfl=opts.cfl,
                                             outputStepping=outputStepping,
                                             structured=structured,
                                             he=he,
                                             nnx=nnx,
                                             nny=nny,
                                             nnz=None,
                                             domain=domain,
                                             initialConditions=initialConditions,
                                             boundaryConditions=None,
                                             auxVariables=auxVariables,
                                             useSuperlu=False)
physical_parameters = myTpFlowProblem.physical_parameters
