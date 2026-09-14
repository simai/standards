"""AI First 1.0 transport facade.

Wire 1.0 deliberately preserves the bounded transport behavior proven by the
0.2 candidate. The shared implementation contains no document-version dispatch;
version-specific discovery and structure checks remain in the 1.0 reader.
"""
from aifirst02_transport import Response, TLSConnection, Transport

__all__ = ['Response', 'TLSConnection', 'Transport']
