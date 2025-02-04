from typing import Sequence, Optional

import geopandas as gpd
import regionmask
from fastapi import APIRouter, Depends, HTTPException
from xpublish import Plugin, hookimpl, Dependencies
from pydantic import PrivateAttr


class EARegionMaskPlugin(Plugin):
    """
    Provides an East Africa (EA) region mask using regionmask and a shapefile.

    Attributes:
        name (str): Plugin name, set to 'ea-regionmask'.
        shapefile_path (str): Path to the shapefile for EA boundaries.
        dataset_router_prefix (str): URL prefix for this router, must start with '/'.
        dataset_router_tags (Sequence[str]): Tags for grouping in API docs.
    """

    name: str = "ea-regionmask"
    shapefile_path: str

    dataset_router_prefix: str = "/ea"  # Must start with '/'
    dataset_router_tags: Sequence[str] = ["EAregion"]

    _gdf: Optional[gpd.GeoDataFrame] = PrivateAttr()
    _ea_regions: Optional[regionmask.Regions] = PrivateAttr()

    def __init__(self, shapefile_path: str):
        """
        Initializes the EARegionMaskPlugin.

        Args:
            shapefile_path (str): File path to the EA shapefile.
        """
        super().__init__(shapefile_path=shapefile_path)

        try:
            gdf = gpd.read_file(shapefile_path)
            object.__setattr__(self, "_gdf", gdf)

            # Construct a regionmask from the first geometry (polygon)
            first_geom = gdf.iloc[0].geometry
            ea_regions = regionmask.Regions(outlines=[first_geom],
                                            names=["EA"],
                                            name="EAregion")
            object.__setattr__(self, "_ea_regions", ea_regions)

        except Exception as e:
            raise RuntimeError(
                f"Failed to load EA shapefile '{shapefile_path}': {e}") from e

    @hookimpl
    def dataset_router(self, deps: Dependencies):
        """Creates a FastAPI router for EA region-specific operations."""
        router = APIRouter(prefix=self.dataset_router_prefix,
                           tags=list(self.dataset_router_tags))

        @router.get("/{var_name}/mean")
        def get_ea_mean(var_name: str, dataset=Depends(deps.dataset)):
            """
            Computes the mean over the EA region for the specified variable.
            """
            if var_name not in dataset.variables:
                raise HTTPException(
                    status_code=404,
                    detail=f"Variable '{var_name}' not found in dataset",
                )

            # Assumes coordinates are labeled 'lat' and 'lon'. Adjust if needed.
            lat_name = "lat"
            lon_name = "lon"
            if lat_name not in dataset or lon_name not in dataset:
                raise HTTPException(
                    status_code=400,
                    detail="Dataset doesn't contain 'lat'/'lon' coords.")

            # Create a 3D mask (dimension: region, lat, lon)
            mask_3d = self._ea_regions.mask_3D(dataset,
                                               lat_name=lat_name,
                                               lon_name=lon_name)
            # Use the first region (assuming only one polygon)
            region_mask = mask_3d.isel(region=0)

            # Subset the data to EA region, compute mean
            data_subset = dataset[var_name].where(region_mask == 1)
            region_mean = data_subset.mean().load()

            # Convert to float, handle NaN
            if region_mean.isnull():
                return {"mean": "NaN"}
            return {
                "plugin": self.name,
                "shapefile_path": self.shapefile_path,
                "variable": var_name,
                "mean": float(region_mean.values),
            }

        return router
