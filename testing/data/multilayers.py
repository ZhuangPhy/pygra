# library to create multilayer systems
from copy import deepcopy
import numpy as np
from scipy.sparse import csc_matrix as csc
from scipy.sparse import bmat

def bilayer_aa(h,t = 0.1):
  """ Creates a bilayer from a honeycomb ribbon"""
  nlayers = 2 # number of layers
  g = h.geometry # get the geometry
  go = deepcopy(g) # copy the geometry
  go.x = [] 
  go.y = []
  go.z = []
  if g.name == "honeycomb_armchair_ribbon": dx ,dy = 1. ,0.
  if g.name == "honeycomb_zigzag_ribbon": dx ,dy = 0. ,-1.
  for (xi,yi) in zip(g.x,g.y):  # modify the geometry
    go.x.append(xi)
    go.x.append(xi+dx)
    go.y.append(yi)
    go.y.append(yi+dy)
    go.z.append(1.)
    go.z.append(-1.)
  go.x,go.y,go.z = np.array(go.x),np.array(go.y),np.array(go.z) # put arrays
  # now modify the hamiltonian
  ho = deepcopy(h)
  n = len(ho.intra) # dimension
  intra = [[0. for i in range(2*n)] for j in range(2*n)]
  inter = [[0. for i in range(2*n)] for j in range(2*n)]
  norb = n # number of orbitals
  # get the atoms which hop according to monolayer type...
  if h.has_spin: 
    norb = norb/2
    tl = [] # interlayer pairs
    x, y, z = go.x, go.y, go.z
    for i in range(len(x)): # loop over atoms
      for j in range(len(x)): # loop over atoms
        if 1.9 < np.abs(z[i]-z[j]) < 2.1: # if in contiguous layers 
          dd = (x[i]-x[j])**2 + (y[i] - y[j])**2 + (z[i] - z[j])**2
          if 3.9<dd<4.1:
            tl.append([i,j])
    for i in range(norb):
      for j in range(norb):  # assign interlayer hopping
        for s in range(2):
         for l in range(nlayers):
          intra[2*nlayers*i+s+2*l][2*nlayers*j+s+2*l] = h.intra[2*i+s,2*j+s]
          inter[2*nlayers*i+s+2*l][2*nlayers*j+s+2*l] = h.inter[2*i+s,2*j+s]
    # now put the interlayer hopping
    for p in tl:
      for s in range(2): # loop over spin
        intra[2*p[0]+s][2*p[1]+s] = t  
        intra[2*p[1]+s][2*p[0]+s] = np.conjugate(t)  
  else: raise # not implemented...
  if h.has_eh: raise # not implemented ....
  ho.intra = np.matrix(intra)
  ho.inter = np.matrix(inter)
  ho.geometry = go
  return ho   



def add_electric_field(h,e = 0.0):
  """Adds electric field to the system"""
  if h.has_spin: # if has spin
    z = h.geometry.z # z coordinates
    g = h.geometry
    for i in range(len(z)):
      if callable(e): efield = e(g.x[i],g.y[i],g.z[i])  # if it is function
      else: efield = e  # if it is number
      h.intra[2*i,2*i] += z[i]*efield
      h.intra[2*i+1,2*i+1] += z[i]*efield
  else: raise 

def multilayered_hamiltonian(h,dr=np.array([0.,0.,0.])):
  """ Creates a multilayered hamiltonian by adding several layers """






def add_interlayer(t,ri,rj,has_spin=True):
  """Calculate interlayer coupling"""
  m = np.matrix([[0. for i in ri] for j in rj])
  if has_spin: m = bmat([[csc(m),None],[None,csc(m)]]).todense()
  zi = [r[2] for r in ri]
  zj = [r[2] for r in rj]
  for i in range(len(ri)): # add the interlayer
    for j in range(len(ri)): # add the interlayer
      rij = ri[i] - rj[j] # distance between atoms
      dz = zi[i] - zj[j] # vertical distance
      if (3.99<rij.dot(rij)<4.01) and (3.99<(dz*dz)<4.01): # check if connect
        if has_spin: # spin polarized
          m[2*i,2*j] = t
          m[2*i+1,2*j+1] = t
        else:  # spin unpolarized
          m[i,j] = t
  return m







def build_honeycomb_bilayer(h,t=0.1,mvl = None ):
  """Builds a multilayer based on a hamiltonian, it is assumed that
  there are no new intercell hoppings in the multilayer"""
  g = h.geometry  # save geometry
  ho = deepcopy(h) # copy the hamiltonian
  go = deepcopy(g) # copy the geometry
  if mvl==None: # if not provided assume firs neighbors
    mvl = g.r[0] - g.r[1]
  def mono2bi(m):
    """Increase the size of the matrices"""    
    return bmat([[csc(m),None],[None,csc(m)]]).todense()  
  # modify the geometry
  x,y,z = np.array(g.x), np.array(g.y) ,np.array(g.z) # store positions
  go.x = np.concatenate([x,x+mvl[0]])  # move 
  go.y = np.concatenate([y,y+mvl[1]])  # move
  go.z = np.concatenate([z-1.0,z+1.0])  # separate two units
  go.xyz2r() # update r coordinates
  if g.has_sublattice: # if has sublattice, keep the indexes
    go.sublattice = g.sublattice*2 # two times
  ho.geometry = go # update geometry
  # modify the hamiltonian
  ho.intra = mono2bi(h.intra)  # increase intracell matrix
  ho.intra += add_interlayer(t,go.r,go.r) # add interlayer coupling
  if h.dimensionality==2: # two dimensional system
    ho.tx = mono2bi(h.tx)  # increase intracell matrix
    ho.ty = mono2bi(h.ty)  # increase intracell matrix
    ho.txy = mono2bi(h.txy)  # increase intracell matrix
    ho.txmy = mono2bi(h.txmy)  # increase intracell matrix
  elif h.dimensionality==1: # one dimensional system
    ho.inter = mono2bi(h.inter)  # increase intercell matrix
    dx = np.array([g.celldis,0.,0.])
    ho.inter += add_interlayer(t,go.r,go.r+dx) # add interlayer coupling
  else:
    raise
  return ho



def build_honeycomb_trilayer(h,t=0.1,mvl=None):
  """Builds a multilayer based on a hamiltonian, it is assumed that
  there are no new intercell hoppings in the multilayer"""
  g = h.geometry  # save geometry
  ho = deepcopy(h) # copy the hamiltonian
  go = deepcopy(g) # copy the geometry
  if mvl==None: # if not provided assume firs neighbors
    mvl = g.r[0] - g.r[1]
  def mono2tri(m):
    """Increase the size of the matrices"""    
    mo = [[None for i in range(3)] for j in range(3)]
    for i in range(3): 
      mo[i][i] = csc(m)
    return bmat(mo).todense()
  # modify the geometry
  x,y,z = np.array(g.x), np.array(g.y) ,np.array(g.z) # store positions
  go.x = np.concatenate([x-mvl[0],x,x+mvl[0]])  # move one unit to the right
  go.y = np.concatenate([y-mvl[1],y,y+mvl[1]])  # leave invariant
  go.z = np.concatenate([z-2.0,z,z+2.0])  # separate two units
  go.xyz2r() # update r coordinates
  if g.has_sublattice: # if has sublattice, keep the indexes
    go.sublattice = g.sublattice*3 # three times
  ho.geometry = go # update geometry
  # modify the hamiltonian
  ho.intra = mono2tri(h.intra)  # increase intracell matrix
  ho.intra += add_interlayer(t,go.r,go.r) # add interlayer coupling
  if h.dimensionality==2: # two dimensional system
    ho.tx = mono2tri(h.tx)  # increase intracell matrix
    ho.ty = mono2tri(h.ty)  # increase intracell matrix
    ho.txy = mono2tri(h.txy)  # increase intracell matrix
    ho.txmy = mono2tri(h.txmy)  # increase intracell matrix
  elif h.dimensionality==1: # one dimensional system
    ho.inter = mono2tri(h.inter)  # increase intercell matrix
    dx = np.array([g.celldis,0.,0.])
    ho.inter += add_interlayer(t,go.r,go.r+dx) # add interlayer coupling
  else:
    raise
  ## add sublattice index, might break
  return ho











