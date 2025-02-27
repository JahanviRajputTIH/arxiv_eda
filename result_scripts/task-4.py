import json
from collections import defaultdict

# Path to JSONL file
jsonl_file = "all_tar_analysis.jsonl"
output_txt = "tar_analysis_results.txt"

def process_jsonl(file_path):
    total_stats = defaultdict(int)
    tar_stats = defaultdict(lambda: defaultdict(int))
    tar_gz_count = defaultdict(set)
    total_gz_with_data = set()

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            tar_name = data.get("tar_file", "unknown")
            stats = data.get("stats", {})
            detailed_analysis = data.get("detailed_analysis", [])
            
            # Aggregate totals
            for key, value in stats.items():
                total_stats[key] += value
            
            # Aggregate per tar file
            for key, value in stats.items():
                tar_stats[tar_name][key] += value
            
            # Track .gz files with data
            for entry in detailed_analysis:
                gz_file = entry.get("file", "unknown")
                analysis = entry.get("analysis", {}).get("files", [])
                
                figures, tables, equations = 0, 0, 0
                missing_figures = 0
                
                for file_analysis in analysis:
                    file_data = file_analysis.get("analysis", {})
                    figures += len(file_data.get("figures", []))
                    tables += file_data.get("tables", 0)
                    equations += file_data.get("equations", 0)
                    missing_figures += len(file_analysis.get("missing_figures", []))
                
                if figures > 0 or tables > 0 or equations > 0:
                    tar_gz_count[tar_name].add(gz_file)
                    total_gz_with_data.add(gz_file)
    
    return total_stats, tar_stats, tar_gz_count, len(total_gz_with_data)

def save_results_to_txt(total_stats, tar_stats, tar_gz_count, total_gz_count, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Overall Dataset Stats:\n")
        for key, value in total_stats.items():
            f.write(f"{key.replace('_', ' ').title()}: {value}\n")
        
        f.write(f"Total .gz files with at least one figure/table/equation: {total_gz_count}\n\n")
        
        f.write("Per TAR Analysis:\n")
        for tar, stats in tar_stats.items():
            f.write(f"TAR: {tar}\n")
            for key, value in stats.items():
                f.write(f"  {key.replace('_', ' ').title()}: {value}\n")
            f.write(f"  .gz files with figures/tables/equations: {len(tar_gz_count[tar])}\n\n")

def main():
    total_stats, tar_stats, tar_gz_count, total_gz_count = process_jsonl(jsonl_file)
    save_results_to_txt(total_stats, tar_stats, tar_gz_count, total_gz_count, output_txt)
    print(f"Results saved to {output_txt}")

if __name__ == "__main__":
    main()
