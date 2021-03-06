from scipy.sparse import coo_matrix,bmat,csc_matrix
import numpy as np


# puts the matrix in spinor form
def m2spin(matin,matin2=[]):
  n=len(matin)
  from numpy import matrix
  if len(matin2)==0:
    matin2=matrix([[0.0j for i in range(n)] for j in range(n)])
  matout=matrix([[0.0j for i in range(2*n)] for j in range(2*n)])
  for i in range(n):
    for j in range(n):
      matout[2*i,2*j]=matin[i,j].copy()
      matout[2*i+1,2*j+1]=matin2[i,j].copy()
  return matout




def spinful(m,m2=None):
  """ Return a spinful hamiltonian"""
  if type(m)==type(np.matrix): return m2spin(m,matin2=m2)
  else: return spinful_sparse(m,m2=m2)


def spinful_sparse(m,m2=None):
  """ Return a spinful hamiltonian"""
  return m2spin_sparse(m,matin2=m2)


def m2spin_sparse(matin,matin2=None):
  m1 = coo_matrix(matin)
  if matin2 is None: m2 = m1
  else: m2 = coo_matrix(matin2)
  rows = np.concatenate([2*m1.row,2*m2.row+1])
  cols = np.concatenate([2*m1.col,2*m2.col+1])
  data = np.concatenate([m1.data,m2.data])
  dim = m1.shape[0]*2
  return csc_matrix((data,(rows,cols)),shape=(dim,dim), dtype=np.complex)
  




def get_spinless2full(h,time_reversal=False):
  """Function to transform a matrix into its full form"""
  if not h.has_spin and not h.has_eh: 
    def outf(m): return m # do nothing
  elif h.has_spin and not h.has_eh: # spinful and no eh
    def outf(m): 
        if time_reversal: return m2spin_sparse(m,np.conjugate(m)) # spinful
        else: return m2spin_sparse(m) # spinful
  elif h.check_mode("spinful_nambu"): # spinful and eh
    from .superconductivity import build_eh
    def outf(m): 
        if time_reversal: m2 = m2spin_sparse(m,np.conjugate(m)) # spinful
        else: m2 = m2spin_sparse(m) # spinful
#        m2 = m2spin_sparse(m) # spinful
        return build_eh(m2) # add e-h
  elif h.check_mode("spinless_nambu"): 
      from .sctk import spinless
      return spinless.nambu
  else: raise
  return outf

  


def get_spinful2full(h):
  """Function to transform a matrix into its full form"""
  if not h.has_spin: raise
  else:
    if h.has_eh:
      from .superconductivity import build_eh
      def outf(m): 
        return build_eh(m) # add e-h
    else:
      def outf(m): return m # do nothing
  return outf




def full2profile(h,profile):
  """Resums a certain profile to show only the spatial dependence"""
  n = len(profile)
  if len(profile)!=h.intra.shape[0]: raise # inconsistency
  if h.has_spin == False and h.has_eh==False: out = np.array(profile)
  elif h.has_spin == True and h.has_eh==False:
    out = np.array([profile[2*i]+profile[2*i+1] for i in range(n//2)])
  elif h.has_spin == False and h.has_eh==True:
    out = np.array([profile[2*i]+profile[2*i+1] for i in range(n//2)])
  elif h.has_spin == True and h.has_eh==True:
    out = np.array([profile[4*i]+profile[4*i+1]+profile[4*i+2]+profile[4*i+3] for i in range(n//4)])
  else: raise # unknown
  if len(out)!=len(h.geometry.r): raise # mistmach in the dimensions
  return out


