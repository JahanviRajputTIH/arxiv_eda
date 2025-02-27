import os
import json
import tarfile
from PyPDF2 import PdfReader
from pathlib import Path
import statistics
import shutil

def count_pdf_pages(directory, file, tar_path):
    pdf_data = []
    page_counts = []

    if not os.path.exists(directory):
        raise ValueError(f"Directory {directory} does not exist")

    for filename in os.listdir(directory):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(directory, filename)
            try:
                reader = PdfReader(file_path)
                num_pages = len(reader.pages)
                entry = {
                    "filepath": f"{tar_path}/{filename}",
                    "page_count": num_pages
                }
                pdf_data.append(entry)
                file.write(json.dumps(entry) + '\n')
                file.flush()
                page_counts.append(num_pages)
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

    stats = {
        "total_files": len(pdf_data),
        "total_pages": sum(page_counts),
        "average_pages": round(statistics.mean(page_counts), 2) if page_counts else 0,
        "median_pages": round(statistics.median(page_counts), 2) if page_counts else 0,
        "std_dev_pages": round(statistics.stdev(page_counts), 2) if len(page_counts) > 1 else 0,
        "min_pages": min(page_counts) if page_counts else 0,
        "max_pages": max(page_counts) if page_counts else 0
    }

    return stats

def process_tar_files(directory):
    current_dir = Path(os.getcwd())
    output_file = current_dir / f"pdf_page_counts.jsonl"
    
    processed_files = []
    corrupted_files = []
    
    with open(output_file, 'a', buffering=1, encoding='utf-8') as f:
        for tar_filename in os.listdir(directory):
            if tar_filename.lower().endswith('.tar'):
                tar_path = os.path.join(directory, tar_filename)
                extract_dir = os.path.join(directory, Path(tar_filename).stem)
                
                print(f"Processing {tar_filename}...")
                try:
                    with tarfile.open(tar_path, 'r') as tar_ref:
                        tar_ref.extractall(extract_dir, filter=None)  # Avoiding DeprecationWarning

                    extracted_subdir = os.path.join(extract_dir, os.listdir(extract_dir)[0])
                    stats = count_pdf_pages(extracted_subdir, f, tar_path)

                    print(f"Done processing {tar_filename}")
                    print(stats)

                    processed_files.append(tar_filename)

                    # Remove the extracted subdirectory after processing
                    shutil.rmtree(extract_dir)
                except Exception as e:
                    print(f"Error processing {tar_filename}: {str(e)}")
                    corrupted_files.append(tar_filename)

    # Final statistics
    print(f"\nProcessing complete. Stats:")
    print(f"Processed .tar files = {len(processed_files)}")
    print(f"Not processed / Corrupted .tar files = {len(corrupted_files)}")
    if corrupted_files:
        print(f"Corrupted .tar files: {', '.join(corrupted_files)}")

def main():
    tar_dir = 'workingData/pdf/'
    process_tar_files(tar_dir)

if __name__ == "__main__":
    main()
