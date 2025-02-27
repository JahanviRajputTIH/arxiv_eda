import json
import sys
from collections import defaultdict

def process_jsonl(file_path):
    tar_summary = defaultdict(lambda: {"total_gz": 0, "total_pdf": 0})
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                data = json.loads(line.strip())
                tar_name = data.get("tar_pair", "Unknown")
                
                gz_count = sum(1 for f in data.get("mapped_files", []) if "source_file" in f)
                pdf_count = sum(1 for f in data.get("mapped_files", []) if "pdf_file" in f)
                
                tar_summary[tar_name]["total_gz"] += gz_count
                tar_summary[tar_name]["total_pdf"] += pdf_count
            except json.JSONDecodeError:
                print("Skipping invalid JSON line", file=sys.stderr)
                continue
    
    return tar_summary

def main():
    file_path = "mapped.jsonl"  # Change this to your actual file path
    output_file = "summary.txt"
    results = process_jsonl(file_path)
    
    total_gz = sum(info["total_gz"] for info in results.values())
    total_pdf = sum(info["total_pdf"] for info in results.values())
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Per Tar Summary:\n")
        for tar, counts in results.items():
            f.write(f"{tar}: .gz = {counts['total_gz']}, .pdf = {counts['total_pdf']}\n")
        
        f.write("\nTotal Mapped Files Across All Tars:\n")
        f.write(f"Total .gz files: {total_gz}\n")
        f.write(f"Total .pdf files: {total_pdf}\n")
    
    print(f"Summary written to {output_file}")

if __name__ == "__main__":
    main()
