__version__ = '1.0.0'
netcdf4_engine = None

try:
    ModuleNotFoundError
except NameError:
    ModuleNotFoundError = ImportError

try:
    import netCDF4 as nc4
    HAS_NETCDF4 = True
except ModuleNotFoundError:
    HAS_NETCDF4 = False
