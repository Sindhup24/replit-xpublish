from typing import Sequence, Optional

import geopandas as gpd
import regionmask
import shapely.geometry as sgeom
from fastapi import APIRouter, Depends, HTTPException
from xpublish import Plugin, hookimpl, Dependencies
from pydantic import PrivateAttr
import xarray as xr


class EARegionMaskPlugin(Plugin):
    """
    Provides a bounding-box region for the 'air_temperature' dataset (lon=200..327, lat=15..75).
    Calls regionmask's mask_3D(dataset) with no lat/lon arguments
    to support older regionmask versions that don't accept lat_name/lon_name.
    """

    name: str = "ea-regionmask"
    dataset_router_prefix: str = "/ea"
    dataset_router_tags: Sequence[str] = ["EAregion"]

    _gdf: Optional[gpd.GeoDataFrame] = PrivateAttr()
    _ea_regions: Optional[regionmask.Regions] = PrivateAttr()

    def __init__(self):
        super().__init__()
        try:
            # Create bounding box: lon=200..327, lat=15..75
            polygon = sgeom.Polygon([(200, 15), (327, 15), (327, 75),
                                     (200, 75)])
            gdf = gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:4326")
            object.__setattr__(self, "_gdf", gdf)

            ea_regions = regionmask.Regions(outlines=gdf.geometry,
                                            names=["EA"],
                                            name="EAregion")
            object.__setattr__(self, "_ea_regions", ea_regions)

        except Exception as e:
            raise RuntimeError(
                f"Failed to build bounding-box region: {e}") from e

    @hookimpl
    def dataset_router(self, deps: Dependencies):
        router = APIRouter(prefix=self.dataset_router_prefix,
                           tags=list(self.dataset_router_tags))

        @router.get("/{var_name}/mean")
        def get_ea_mean(var_name: str, dataset=Depends(deps.dataset)):
            # 1) Check variable
            if var_name not in dataset.variables:
                raise HTTPException(
                    status_code=404,
                    detail=f"Variable '{var_name}' not found in dataset",
                )

            # 2) regionmask with NO lat/lon arguments
            #    This should work if your dataset has dims named exactly 'lat','lon'.
            mask_3d = self._ea_regions.mask_3D(dataset)
            region_mask = mask_3d.isel(region=0)

            data_subset = dataset[var_name].where(region_mask == 1)
            region_mean = data_subset.mean().load()

            if region_mean.isnull():
                return {"mean": "NaN"}
            return {
                "plugin": self.name,
                "region": "BBox(lon=200..327, lat=15..75)",
                "variable": var_name,
                "mean": float(region_mean.values),
            }

        return router
