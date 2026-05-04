import os
import shutil
from pathlib import Path

REQUIRED_FILES = {
    "TCI_10m.jp2": "tci.jp2",
    "B04_10m.jp2": "b04.jp2",
    "B08_10m.jp2": "b08.jp2",
    "B11_20m.jp2": "b11.jp2",
    "B8A_20m.jp2": "b8a.jp2",
    "SCL_20m.jp2": "scl.jp2",
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "dataset" / "raw_dataset"
FINAL_DIR = PROJECT_ROOT / "dataset" / "final_dataset"


def find_required_files(root_folder: Path):
    found = {}
    for root, _, files in os.walk(root_folder):
        for f in files:
            for req_name in REQUIRED_FILES:
                if f.endswith(req_name):
                    found[req_name] = Path(root) / f
    return found


def final_dataset_ready(city_name: str):
    city_folder = FINAL_DIR / f"{city_name.lower()}_dataset"
    if not city_folder.exists():
        return False

    for _, new_name in REQUIRED_FILES.items():
        if not (city_folder / new_name).exists():
            return False

    return True


def process_raw_folder(city_name: str, raw_folder: Path):
    city_final_folder = FINAL_DIR / f"{city_name.lower()}_dataset"
    city_final_folder.mkdir(parents=True, exist_ok=True)

    found = find_required_files(raw_folder)

    missing = [x for x in REQUIRED_FILES if x not in found]
    if missing:
        raise FileNotFoundError(f"Missing required Sentinel files: {missing}")

    for original, renamed in REQUIRED_FILES.items():
        src = found[original]
        dst = city_final_folder / renamed
        shutil.copy2(src, dst)

    with open(city_final_folder / "dataset_log.txt", "w", encoding="utf-8") as f:
        f.write(f"City: {city_name}\n")
        f.write(f"Raw folder: {raw_folder}\n\nCopied files:\n")
        for original, renamed in REQUIRED_FILES.items():
            f.write(f"{original} -> {renamed}\n")

    print(f"[OK] Extracted dataset saved to: {city_final_folder}")


def delete_raw_folder(raw_folder: Path):
    try:
        shutil.rmtree(raw_folder)
        print(f"[OK] Deleted raw folder: {raw_folder}")
    except Exception as e:
        print(f"[WARNING] Could not delete raw folder: {e}")


def run_pipeline(city_name: str, raw_folder_name: str):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    raw_folder = RAW_DIR / raw_folder_name

    if not raw_folder.exists():
        raise FileNotFoundError(f"Raw folder not found: {raw_folder}")

    if final_dataset_ready(city_name):
        print(f"[SKIP] Final dataset already exists for {city_name}. Deleting raw folder only.")
        delete_raw_folder(raw_folder)
        return

    process_raw_folder(city_name, raw_folder)
    delete_raw_folder(raw_folder)


if __name__ == "__main__":
    print("\n=== Sentinel Dataset Manager ===\n")
    print(f"Raw dataset folder:   {RAW_DIR}")
    print(f"Final dataset folder: {FINAL_DIR}\n")

    city = input("Enter city name (example: lucknow): ").strip().lower()
    raw_name = input("Enter raw folder name inside raw_dataset (any name): ").strip()

    run_pipeline(city, raw_name)