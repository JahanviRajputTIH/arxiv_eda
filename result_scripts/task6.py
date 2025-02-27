import os
import jsonlines
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# Constants
JSONL_FILE = "../jsonOutputs/pdf_page_counts.jsonl"
BASE_RESULTS_DIR = "result_script_outputs/task6/"
OVERALL_RESULTS_DIR = os.path.join(BASE_RESULTS_DIR, "overall")
os.makedirs(OVERALL_RESULTS_DIR, exist_ok=True)

# Ensure subdirectories exist
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def log_and_print(message, log_path):
    print(message)
    with open(log_path, "a") as f:
        f.write(message + "\n")

def analyze_jsonl_file(jsonl_file):
    total_pdfs = 0
    total_pages = 0
    page_counts = []
    subdir_stats = defaultdict(lambda: {
        "total_pdfs": 0, "total_pages": 0, "page_counts": [], "file_data": []
    })

    with jsonlines.open(jsonl_file) as reader:
        for obj in reader:
            filepath = obj["filepath"]
            page_count = obj["page_count"]
            subdir = filepath.split("/")[-2]
            filename = filepath.split("/")[-1]

            total_pdfs += 1
            total_pages += page_count
            page_counts.append(page_count)

            subdir_stats[subdir]["total_pdfs"] += 1
            subdir_stats[subdir]["total_pages"] += page_count
            subdir_stats[subdir]["page_counts"].append(page_count)
            subdir_stats[subdir]["file_data"].append((filename, page_count))
    
    return total_pdfs, total_pages, page_counts, subdir_stats

def calculate_statistics(page_counts):
    if not page_counts:
        return 0, 0, 0, 0
    return np.mean(page_counts), np.max(page_counts), np.min(page_counts), np.std(page_counts)

def get_filename_from_stat(subdir_stats, subdir, is_max=True):
    if subdir and subdir_stats[subdir]["file_data"]:
        return max(subdir_stats[subdir]["file_data"], key=lambda x: x[1]) if is_max else min(subdir_stats[subdir]["file_data"], key=lambda x: x[1])
    return ("None", 0)

def save_plot(data, title, xlabel, ylabel, save_path):
    plt.figure()
    plt.hist(data, bins=50, alpha=0.75)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid()
    plt.savefig(save_path)
    plt.close()

def main():
    log_file = os.path.join(OVERALL_RESULTS_DIR, "task6.txt")
    log_and_print("===== Task 6: Analyzing JSONL File =====", log_file)
    total_pdfs, total_pages, page_counts, subdir_stats = analyze_jsonl_file(JSONL_FILE)

    max_pdfs_subdir = max(subdir_stats, key=lambda x: subdir_stats[x]["total_pdfs"], default=None)
    min_pdfs_subdir = min(subdir_stats, key=lambda x: subdir_stats[x]["total_pdfs"], default=None)
    max_pages_subdir = max(subdir_stats, key=lambda x: subdir_stats[x]["total_pages"], default=None)
    min_pages_subdir = min(subdir_stats, key=lambda x: subdir_stats[x]["total_pages"], default=None)
    max_mean_subdir = max(subdir_stats, key=lambda x: np.mean(subdir_stats[x]["page_counts"]) if subdir_stats[x]["page_counts"] else 0, default=None)
    min_mean_subdir = min(subdir_stats, key=lambda x: np.mean(subdir_stats[x]["page_counts"]) if subdir_stats[x]["page_counts"] else 0, default=None)
    max_page_file, max_page_file_subdir = max(((f, s) for s in subdir_stats for f in subdir_stats[s]["file_data"]), key=lambda x: x[0][1], default=(("None", 0), "None"))
    min_page_file, min_page_file_subdir = min(((f, s) for s in subdir_stats for f in subdir_stats[s]["file_data"]), key=lambda x: x[0][1], default=(("None", 0), "None"))
    
    log_and_print(f"Total PDFs: {total_pdfs} (Max in {max_pdfs_subdir}: {subdir_stats[max_pdfs_subdir]['total_pdfs']}, Min in {min_pdfs_subdir}: {subdir_stats[min_pdfs_subdir]['total_pdfs']})", log_file)
    log_and_print(f"Total Pages: {total_pages} (Max in {max_pages_subdir}: {subdir_stats[max_pages_subdir]['total_pages']}, Min in {min_pages_subdir}: {subdir_stats[min_pages_subdir]['total_pages']})", log_file)
    log_and_print(f"Mean Pages per PDF: {np.mean(page_counts):.2f} (Max in {max_mean_subdir}: {np.mean(subdir_stats[max_mean_subdir]['page_counts']):.2f}, Min in {min_mean_subdir}: {np.mean(subdir_stats[min_mean_subdir]['page_counts']):.2f})", log_file)
    log_and_print(f"Max Pages per PDF: {max_page_file[1]} (File: {max_page_file[0]}, Subdir: {max_page_file_subdir})", log_file)
    log_and_print(f"Min Pages per PDF: {min_page_file[1]} (File: {min_page_file[0]}, Subdir: {min_page_file_subdir})", log_file)

    # Save plots
    save_plot(page_counts, "PDF Page Counts Distribution", "Pages", "Frequency", os.path.join(OVERALL_RESULTS_DIR, "page_counts_hist.png"))
    
    # Save subdirectory analysis
    for subdir, stats in subdir_stats.items():
        subdir_path = os.path.join(BASE_RESULTS_DIR, subdir)
        ensure_dir(subdir_path)
        
        max_page_file, min_page_file = get_filename_from_stat(subdir_stats, subdir, True), get_filename_from_stat(subdir_stats, subdir, False)
        
        with open(os.path.join(subdir_path, "stats.txt"), "w") as f:
            f.write(f"Total PDFs: {stats['total_pdfs']}\n")
            f.write(f"Total Pages: {stats['total_pages']}\n")
            f.write(f"Mean Pages per PDF: {np.mean(stats['page_counts']):.2f}\n")
            f.write(f"Max Pages per PDF: {max_page_file[1]} (File: {max_page_file[0]})\n")
            f.write(f"Min Pages per PDF: {min_page_file[1]} (File: {min_page_file[0]})\n")
        
        save_plot(stats["page_counts"], f"{subdir} PDF Page Counts", "Pages", "Frequency", os.path.join(subdir_path, "page_counts_hist.png"))

if __name__ == "__main__":
    main()
