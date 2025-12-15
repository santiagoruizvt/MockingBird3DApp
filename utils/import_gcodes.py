"""
Script to import .gcode files from a folder into the Flask app as Orders.

Behavior:
- Scan a folder for .gcode files (non-recursive by default).
- For each file found, parse metadata using `gcode_parser.parse_gcode`.
- Create an `Order` record with fields populated from metadata:
  - name: filename without extension
  - client: 'Imported'
  - weight_grams: estimated filament weight in grams (if present) else 0
  - material: try to match an existing Material by name (case-insensitive)
  - print_time_hours: parsed time in hours
  - status: 'En proceso'
  - quantity: 1 (default)
- After successful import, move the .gcode to a `processed/` subfolder to avoid double-import.

Usage:
  python utils/import_gcodes.py /path/to/gcodes --processed-dir processed

You can run this periodically (cron/Task Scheduler) or adapt it to run continuously with watchdog.
"""

import os
import shutil
import argparse
from pathlib import Path

# Ensure project root is on sys.path so `from utils...` imports work when running this script directly
import sys
HERE = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.gcode_parser import parse_gcode

# Import Flask app and models
from app import app, db
from models import Order, Material


def find_material_by_name(name: str):
    if not name:
        return None
    # simple case-sensitive match first
    m = Material.query.filter_by(name=name).first()
    if m:
        return m
    # fallback: case-insensitive
    m = Material.query.filter(Material.name.ilike(name)).first()
    return m


def import_folder(folder_path: str, processed_dir: str = "processed"):
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"Folder does not exist: {folder_path}")

    processed_path = folder / processed_dir
    processed_path.mkdir(exist_ok=True)

    imported = []
    errors = []

    with app.app_context():
        for entry in folder.iterdir():
            if not entry.is_file():
                continue
            if entry.suffix.lower() not in (".gcode", ".gc", ".gco", ".g"):
                continue

            # Skip already processed folder
            if entry.parent == processed_path:
                continue

            try:
                meta = parse_gcode(str(entry))

                # If an Order already exists with the same name and status 'En proceso' or 'Terminado',
                # we still import a new order (you may change this behavior). To avoid exact duplicates,
                # you could check for an Order with a custom source_path field; this script uses move-to-processed.

                name_noext = entry.stem
                client = "Imported"
                weight_grams = meta.get("filament_weight_g") or 0.0
                material_name = meta.get("material")
                material = find_material_by_name(material_name) if material_name else None
                print_time_hours = meta.get("time_hours") or 0.0

                order = Order(
                    name=name_noext,
                    client=client,
                    weight_grams=float(weight_grams),
                    material_id=material.id if material else None,
                    print_time_hours=float(print_time_hours),
                    status="En proceso",
                )
                db.session.add(order)
                db.session.commit()

                # move file to processed folder
                dest = processed_path / entry.name
                shutil.move(str(entry), str(dest))

                imported.append({"file": str(entry), "order_id": order.id})
                print(f"Imported {entry.name} -> Order id {order.id}")

            except Exception as e:
                errors.append({"file": str(entry), "error": str(e)})
                print(f"Error importing {entry.name}: {e}")

    return imported, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import .gcode files in a folder as Orders in the Flask app")
    parser.add_argument("folder", help="Folder containing .gcode files")
    parser.add_argument("--processed-dir", default="processed", help="Subfolder to move processed files into")

    args = parser.parse_args()
    imported, errors = import_folder(args.folder, args.processed_dir)

    print("Done.")
    print("Imported:", imported)
    if errors:
        print("Errors:", errors)
