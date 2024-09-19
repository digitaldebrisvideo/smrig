"""
Like the 'Deform' menu in Maya, this deals with non-linears, wraps, lattices
etc and nothing about skin clusters. As skin clusters and joints are such a
big part of what we do they are split into two different libs, *kinematicslib*
for joints and *skinninglib* for any thing skinning related.
"""
from . import cluster
from . import geometry
from . import io
from . import skincluster
from . import soft_mod
from . import wrap
from . import xml
