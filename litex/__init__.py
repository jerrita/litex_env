import sys
import os

from litex.tools.litex_client import RemoteClient

# Python-Data Import Helper ------------------------------------------------------------------------

# def get_data_mod(data_type, data_name):
#     """Get the pythondata-{}-{} module or raise a useful error message."""
#     imp = "import pythondata_{}_{} as dm".format(data_type, data_name)
#     try:
#         l = {}
#         exec(imp, {}, l)
#         dm = l['dm']
#         return dm
#     except ImportError as e:
#         raise ImportError("""\
# pythondata-{dt}-{dn} module not installed! Unable to use {dn} {dt}.
# {e}

# You can install this by running;
#  pip3 install git+https://github.com/litex-hub/pythondata-{dt}-{dn}.git
# """.format(dt=data_type, dn=data_name, e=e)) from None


class DummyDataModule:
    data_location = None

def get_data_mod(data_type, data_name):
    # get file directory
    file_dir = os.path.dirname(os.path.abspath(__file__))
    # get the parent directory
    parent_dir = os.path.dirname(file_dir)
    res = DummyDataModule()
    res.data_location = os.path.join(parent_dir, "data_mod")
    return res