#!/usr/bin/env python3
"""
Kraken Audit — Lambda Deployment Packager
Bundles the entire kraken_audit module into a Lambda-compatible zip.
"""

import os
import zipfile
import shutil
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INGESTION = os.path.join(ROOT, "ingestion")
OUTPUT_ZIP = os.path.join(INGESTION, "infra", "lambda_function_payload.zip")
EXCLUDES = {"__pycache__", ".git", ".env", "venv", "chroma_kb", "docs/reports", "invoices", "tests"}

def package():
    print("📦 Kraken Audit Lambda Packager")
    print("=" * 45)

    # Collect all files from kraken_audit
    files_to_zip = []
    for root_dir, dirs, files in os.walk(ROOT):
        # Skip excluded dirs
        rel = os.path.relpath(root_dir, ROOT)
        parts = rel.split(os.sep)
        if any(p in EXCLUDES for p in parts):
            continue
        for f in files:
            if f.endswith(".pyc"):
                continue
            fpath = os.path.join(root_dir, f)
            # Relative path from ROOT
            arcname = os.path.relpath(fpath, os.path.dirname(ROOT))
            files_to_zip.append((fpath, arcname))

    # Write zip
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath, arcname in files_to_zip:
            zf.write(fpath, arcname)

    size_mb = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)
    print(f"  ✅ {len(files_to_zip)} files bundled")
    print(f"  📦 {OUTPUT_ZIP}")
    print(f"  💾 {size_mb:.1f} MB")
    print("=" * 45)
    print("  ✅ Ready for: terraform apply")

if __name__ == "__main__":
    package()