#!/usr/bin/env python3
"""
GeoComfortIQ — Quick Setup Script
Run this once after extracting the project zip:
    python setup.py
"""

import os
import sys
import subprocess
import shutil


def run(cmd, **kwargs):
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, **kwargs)
    if result.returncode != 0:
        print(f"[WARNING] Command exited with code {result.returncode}")
    return result.returncode


def main():
    print("=" * 60)
    print("  GeoComfortIQ — Project Setup")
    print("=" * 60)

    # 1. Create .env from example if not exists
    if not os.path.exists(".env") and os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
        print("\n[OK] Created .env from .env.example")
        print("     Edit .env to add your API keys (optional)")

    # 2. Install dependencies
    print("\n[1/4] Installing Python dependencies...")
    run(f"{sys.executable} -m pip install -r requirements.txt")

    # 3. Run migrations
    print("\n[2/4] Running database migrations...")
    run(f"{sys.executable} manage.py makemigrations")
    run(f"{sys.executable} manage.py migrate")

    # 4. Collect static files
    print("\n[3/4] Collecting static files...")
    run(f"{sys.executable} manage.py collectstatic --noinput")

    # 5. Create data/cities directory reminder
    print("\n[4/4] Checking satellite image directory...")
    os.makedirs("data/cities", exist_ok=True)
    images_exist = any(
        f.lower().endswith(('.jpg', '.png', '.tif'))
        for f in os.listdir("data/cities")
    ) if os.path.exists("data/cities") else False

    print("\n" + "=" * 60)
    print("  Setup Complete!")
    print("=" * 60)
    print("\nTo start the server:")
    print("    python manage.py runserver")
    print("\nThen open: http://127.0.0.1:8000")

    if not images_exist:
        print("\n[NOTE] No satellite images found in data/cities/")
        print("       The app will use realistic mock data.")
        print("       To use real satellite imagery:")
        print("       1. Download from ISRO Bhuvan or Sentinel Hub")
        print("       2. Save as: data/cities/lucknow.jpg")
        print("       3. Supported cities: lucknow, delhi, mumbai,")
        print("          bengaluru, hyderabad, chennai, kolkata, jaipur")

    print("\nAdmin panel: http://127.0.0.1:8000/admin/")
    print("Docs folder: /docs/README.md\n")


if __name__ == "__main__":
    main()
