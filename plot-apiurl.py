import requests
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import shapely.geometry as sgeom
import geopandas as gpd

def create_synthetic_data():
    """
    Create a random 2D dataset with lat=15..75, lon=200..327
    Returns an xarray.Dataset with coords [lat, lon] and variable 'temp'.
    """
    lat = np.arange(15, 76, 2.0)   # from 15 to 75 in steps of 2
    lon = np.arange(200, 328, 2.0) # from 200 to 327 in steps of 2

    data = np.random.rand(lat.size, lon.size) * 10 + 280  # random around 280..290 K
    ds = xr.Dataset(
        {"temp": (("lat", "lon"), data)},
        coords={"lat": lat, "lon": lon}
    )
    return ds

def fetch_polygon_from_api(api_url):
    """
    Fetch the bounding box polygon as GeoJSON from the EARegionMaskPlugin's /polygon endpoint,
    then convert it into a GeoDataFrame.
    """
    response = requests.get(api_url)
    if not response.ok:
        raise RuntimeError(f"Failed to fetch polygon from {api_url}: {response.text}")

    polygon_geojson = response.json()
    gdf = gpd.GeoDataFrame.from_features(polygon_geojson, crs="EPSG:4326")
    return gdf

def plot_data_and_polygon(ds, gdf):
    fig = plt.figure(figsize=(8, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Focus on the EA region
    ax.set_extent([200, 327, 15, 75], ccrs.PlateCarree())

    ds.temp.plot(
        ax=ax,
        x="lon",
        y="lat",
        transform=ccrs.PlateCarree(),
        cmap="coolwarm",
        cbar_kwargs={"label": "Synthetic Temperature (K)"},
    )

    gdf.boundary.plot(ax=ax, edgecolor="black")

    ax.coastlines()
    ax.set_title("Synthetic Data with EA Bounding Box (Zoomed to EA Region)")
    plt.show()


def main():
    # 1) Create synthetic data locally
    ds = create_synthetic_data()

    # 2) Fetch the polygon from your EARegionMaskPlugin's /polygon route
    # Example URL: "https://<YOUR-REPL-URL>.replit.dev:9000/datasets/air_temperature/ea/polygon"
    # Adjust for your server's URL and dataset_id
    api_url = "https://fc986e6b-1e35-48f0-a606-8cdb8f3313fa-00-10hxripuav3fp.picard.replit.dev/datasets/air_temperature/ea/polygon"
    gdf_polygon = fetch_polygon_from_api(api_url)

    # 3) Plot data and fetched polygon
    plot_data_and_polygon(ds, gdf_polygon)

if __name__ == "__main__":
    main()
