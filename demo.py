import xarray as xr
from requests import HTTPError
import cf_xarray
import rioxarray

from xpublish import Plugin, Rest, hookimpl


class TutorialDataset(Plugin):
    name: str = "xarray-tutorial-datasets"

    @hookimpl
    def get_datasets(self):
        return list(xr.tutorial.file_formats)

    @hookimpl
    def get_dataset(self, dataset_id: str):
        try:
            ds = xr.tutorial.open_dataset(dataset_id)
            if ds.cf.coords["longitude"].dims[0] == "longitude":
                ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360) -
                                      180).sortby("longitude")
                ds = ds.rio.write_crs(4326)
            return ds
        except HTTPError:
            return None


rest = Rest({})
rest.register_plugin(TutorialDataset())

from lme import LmeSubsetPlugin
from mean import MeanPlugin
from ea_regionmask_plugin import EARegionMaskPlugin

rest.register_plugin(MeanPlugin())
rest.register_plugin(LmeSubsetPlugin())
rest.register_plugin(EARegionMaskPlugin("ea_adm0_geoboundaries.shp"))

rest.serve()
