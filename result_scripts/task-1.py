import json
import collections

def process_jsonl(file_path, output_file):
    total_missing = 0
    missing_gz = 0
    missing_pdf = 0
    tar_file_counts = collections.defaultdict(lambda: {"missing_gz": 0, "missing_pdf": 0})

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            total_missing += 1
            data = json.loads(line.strip())
            path = data["path"]
            status = data["status"]

            # Extract tar file name (e.g., "arXiv_pdf_2310_104.tar")
            tar_file = path.split("/")[-2]

            if "Missing .gz" in status:
                missing_gz += 1
                tar_file_counts[tar_file]["missing_gz"] += 1
            elif "Missing .pdf" in status:
                missing_pdf += 1
                tar_file_counts[tar_file]["missing_pdf"] += 1

    results = {
        "total_missing": total_missing,
        "missing_gz": missing_gz,
        "missing_pdf": missing_pdf,
        "tar_file_details": dict(tar_file_counts)
    }

    # Save results to a JSON file
    with open(output_file, "w", encoding="utf-8") as out_f:
        json.dump(results, out_f, indent=4)

    print(f"Results saved to {output_file}")

# Example Usage
file_path = "mapping.jsonl"  # Replace with actual path
output_file = "output_results.json"

process_jsonl(file_path, output_file)
