from huggingface_hub import HfFileSystem

fs = HfFileSystem()
data_path = "datasets/maduschek/LAMES/data"

print(f"Inspecting contents of {data_path}...")
try:
    contents = fs.ls(data_path, detail=False)
    # Just show the first 15 items so we don't spam your terminal
    for item in contents[:15]:
        print(f" - {item}")
    if len(contents) > 15:
        print(f" ... and {len(contents) - 15} more items.")
except Exception as e:
    print(f"Error accessing repository: {e}")
