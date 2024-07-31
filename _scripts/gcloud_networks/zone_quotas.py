import subprocess
import json
import concurrent.futures

def get_quota_for_region(region):
    try:
        command = f"gcloud compute regions describe {region} --format=json"
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        region_info = json.loads(result.stdout)
        return region, region_info["quotas"], region_info["zones"]
    except subprocess.CalledProcessError as e:
        return region, str(e), []

regions = [
    "us-east1", "us-east4", "us-central1", "us-west1",
    "europe-west4", "europe-west1", "europe-west3", "europe-west2",
    "asia-east1", "asia-southeast1", "asia-northeast1", "asia-south1",
    "australia-southeast1", "southamerica-east1", "africa-south1",
    "asia-east2", "asia-northeast2", "asia-northeast3", "asia-south2",
    "asia-southeast2", "australia-southeast2", "europe-central2",
    "europe-north1", "europe-southwest1", "europe-west10", "europe-west12",
    "europe-west6", "europe-west8", "europe-west9", "me-central1", "me-central2",
    "me-west1", "northamerica-northeast1", "northamerica-northeast2",
    "southamerica-west1", "us-east5", "us-south1", "us-west2",
    "us-west3", "us-west4"
]

def main():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_region = {executor.submit(get_quota_for_region, region): region for region in regions}
        for future in concurrent.futures.as_completed(future_to_region):
            region = future_to_region[future]
            try:
                region, quotas, zones = future.result()
                zones_list = [zone.split('/')[-1] for zone in zones]
                print(f"Region: {region} (Zones: {', '.join(zones_list)})")
                if isinstance(quotas, str):
                    print(f"Error: {quotas}")
                else:
                    for quota in quotas:
                        if quota['metric'] == "CPUS":
                            print(f"{quota['metric']}: {quota['usage']} / {quota['limit']}")
            except Exception as e:
                print(f"Failed to get quotas for region {region}: {e}")

if __name__ == "__main__":
    main()