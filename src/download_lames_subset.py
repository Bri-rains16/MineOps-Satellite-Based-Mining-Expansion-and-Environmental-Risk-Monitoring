from huggingface_hub import hf_hub_download

repo_id = "maduschek/LAMES"
# We are picking just the first chunk of train and test
subset_files = [
    "data/train-00000-of-00027.parquet",
    "data/test-00000-of-00008.parquet"
]

print("Downloading LAMES subset (1 train chunk, 1 test chunk)...")
for file_path in subset_files:
    print(f"Fetching {file_path}...")
    hf_hub_download(
        repo_id=repo_id,
        filename=file_path,
        repo_type="dataset",
        local_dir="data/lames"
    )

print("Subset download complete! Check the data/lames/data folder.")
