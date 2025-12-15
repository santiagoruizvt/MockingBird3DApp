import re
import os
from typing import Optional, Dict

TIME_PATTERN = re.compile(r"TIME\s*:\s*(\d+)", re.IGNORECASE)
ESTIMATED_TIME_PATTERN = re.compile(r"Estimated printing time.*?:\s*(.*)", re.IGNORECASE)
MATERIAL_PATTERN = re.compile(r"Material\s*:\s*(.+)", re.IGNORECASE)
FILAMENT_WEIGHT_PATTERN = re.compile(r"Estimated filament weight\s*:\s*([0-9.]+)g", re.IGNORECASE)

HMS_PATTERN = re.compile(r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?", re.IGNORECASE)


def parse_time_hms_to_seconds(hms_str: str) -> int:
    """Parse strings like '1h 15m 23s' or '75m 23s' into seconds."""
    if not hms_str or not hms_str.strip():
        return 0
    m = HMS_PATTERN.search(hms_str)
    if not m:
        # try to extract numbers
        nums = re.findall(r"(\d+)", hms_str)
        if nums:
            # assume last number is seconds if 1 number then seconds
            if len(nums) == 1:
                return int(nums[0])
        return 0
    h = int(m.group(1)) if m.group(1) else 0
    mm = int(m.group(2)) if m.group(2) else 0
    s = int(m.group(3)) if m.group(3) else 0
    return h * 3600 + mm * 60 + s


def parse_gcode(file_path: str) -> Dict[str, Optional[object]]:
    """Parse a single .gcode file and extract name, material and time (seconds/hours).

    Returns a dict: { 'path', 'name', 'material', 'time_seconds', 'time_hours' }
    """
    name = os.path.basename(file_path)
    material = None
    time_seconds = None
    filament_weight_g = None

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                # only inspect comment/metadata lines (start with ';' or '(')
                if not line:
                    continue
                if line.startswith(";"):
                    content = line[1:].strip()
                elif line.startswith("(") and line.endswith(")"):
                    content = line[1:-1].strip()
                else:
                    continue

                # Check TIME: (seconds)
                m_time = TIME_PATTERN.search(content)
                if m_time and time_seconds is None:
                    try:
                        time_seconds = int(m_time.group(1))
                    except ValueError:
                        pass
                    continue

                # Estimated printing time (human readable)
                m_est = ESTIMATED_TIME_PATTERN.search(content)
                if m_est and time_seconds is None:
                    hms = m_est.group(1).strip()
                    sec = parse_time_hms_to_seconds(hms)
                    if sec:
                        time_seconds = sec
                    continue

                # Estimated filament weight (grams)
                m_w = FILAMENT_WEIGHT_PATTERN.search(content)
                if m_w and filament_weight_g is None:
                    try:
                        filament_weight_g = float(m_w.group(1))
                    except ValueError:
                        filament_weight_g = None
                    continue

                # Material
                m_mat = MATERIAL_PATTERN.search(content)
                if m_mat and material is None:
                    material = m_mat.group(1).strip()
                    continue

    except FileNotFoundError:
        raise

    # Fallback: if time not found set to 0
    if time_seconds is None:
        time_seconds = 0

    time_hours = round(time_seconds / 3600.0, 4)

    return {
        "path": file_path,
        "name": name,
        "material": material,
        "time_seconds": time_seconds,
        "time_hours": time_hours,
        "filament_weight_g": filament_weight_g,
    }


def parse_folder(folder_path: str, extensions=None):
    """Parse all gcode files in a folder (non-recursive by default). Returns list of dicts."""
    if extensions is None:
        extensions = [".gcode", ".gc", ".gco", ".g"]
    results = []
    for entry in os.scandir(folder_path):
        if not entry.is_file():
            continue
        _, ext = os.path.splitext(entry.name)
        if ext.lower() in extensions:
            try:
                info = parse_gcode(entry.path)
                results.append(info)
            except Exception as e:
                results.append({"path": entry.path, "error": str(e)})
    return results


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Parse .gcode files and extract metadata (name, material, time in hours).")
    parser.add_argument("path", help="Path to a .gcode file or a directory containing .gcode files")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()
    p = args.path
    out = []
    if os.path.isdir(p):
        out = parse_folder(p)
    else:
        out = [parse_gcode(p)]

    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        for item in out:
            if "error" in item:
                print(f"{item['path']}: ERROR: {item['error']}")
                continue
            print(f"File: {item['name']}")
            print(f"  Path: {item['path']}")
            print(f"  Material: {item['material']}")
            print(f"  Time (s): {item['time_seconds']}")
            print(f"  Time (h): {item['time_hours']}")
            print()
