# -*- coding: utf-8 -*-
"""
catastro-espana
Librería oficial de RefCatastral.es para consultar Catastro (DGC) y SIGPAC (FEGA) en España.
"""

from .client import Catastro, InmuebleCatastral
from .sigpac import Sigpac, ParcelaSigpac, RecintoSigpac, USOS_SIGPAC

__version__ = "1.0.0"
__author__ = "RefCatastral.es"
__all__ = [
    "Catastro",
    "Sigpac",
    "InmuebleCatastral",
    "ParcelaSigpac",
    "RecintoSigpac",
    "USOS_SIGPAC",
]
