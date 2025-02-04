import requests
import xarray as xr

# Use your Replit-provided URL:
BASE_URL = "https://fc986e6b-1e35-48f0-a606-8cdb8f3313fa-00-10hxripuav3fp.picard.replit.dev"

def call_endpoint(path: str):
    """Helper to send GET requests, print status and partial response."""
    url = f"{BASE_URL}{path}"
    print(f"\n--- GET {url} ---")
    try:
        resp = requests.get(url)
        print("Status:", resp.status_code)
        if resp.status_code == 200:
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type.lower():
                print("JSON:", resp.json())
            else:
                print("Response text snippet:", resp.text[:200], "...")
        else:
            print("Error text snippet:", resp.text[:200], "...")
    except Exception as exc:
        print("Exception:", exc)

# 1. Call base routes
call_endpoint("/")        # (Root - may or may not return anything)
call_endpoint("/docs")    # (OpenAPI documentation)
call_endpoint("/datasets")# (List of dataset IDs)

# Example lists for demonstration.
# Adjust these based on your known dataset IDs, variable names, region IDs, etc.
DATASET_IDS = ["air_temperature"]  # (Replace with actual dataset IDs)
VARIABLES = ["air"]                # (Replace with actual variable in your dataset)
LME_REGION_IDS = ["EC"]            # (Replace with region from your LmeSubsetPlugin)

# 2a. LME plugin routes
#    i) The "app_router": /lme
call_endpoint("/lme")

#    ii) Subset route: /datasets/{dataset_id}/lme/{region_id}
for ds_id in DATASET_IDS:
    for region_id in LME_REGION_IDS:
        path_subset = f"/datasets/{ds_id}/lme/{region_id}"
        call_endpoint(path_subset)

# 2b. Mean plugin route: /datasets/{dataset_id}/{var_name}/mean
for ds_id in DATASET_IDS:
    for var_name in VARIABLES:
        path_mean = f"/datasets/{ds_id}/{var_name}/mean"
        call_endpoint(path_mean)

# 2c. EAregion plugin route: /datasets/{dataset_id}/ea/{var_name}/mean
for ds_id in DATASET_IDS:
    for var_name in VARIABLES:
        path_ea_mean = f"/datasets/{ds_id}/ea/{var_name}/mean"
        call_endpoint(path_ea_mean)
