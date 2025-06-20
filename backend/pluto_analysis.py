import subprocess
import json

def run_pluto(path: str) -> list:
    cmd = ["pluto", "detect-files", "-o", "json", "-d", path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Pluto returns exit code 3 when it finds deprecated APIs (this is normal)
    if result.returncode in [0, 3]:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return []
    else:
        # If there's a real error, return empty list
        print(f"Pluto error: {result.stderr}")
        return []

