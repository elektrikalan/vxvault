import csv
import os

def export_to_csv(records, filename="export.csv"):
    os.makedirs("exports", exist_ok=True)
    filepath = os.path.join("exports", filename)
    
    headers = ["Date", "URL", "MD5", "IP", "Tools", "SHA1", "SHA256", "Size"]
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(records)
    
    return filepath
