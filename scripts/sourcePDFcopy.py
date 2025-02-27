import os
import tarfile
import shutil
import json
import time
from pathlib import Path
import re

def process_tar_file(tar_file_path, target_dir, output_jsonl, processed_files, corrupted_files):
    """Extracts PDFs from a .tar file and saves results in a JSONL file."""
    tar_name_without_ext = os.path.splitext(os.path.basename(tar_file_path))[0]
    target_subdir = os.path.join(target_dir, f"{tar_name_without_ext}_test")
    os.makedirs(target_subdir, exist_ok=True)

    start_time = time.time()
    pdfs_copied = []

    try:
        print(f"Processing {tar_file_path}...")
        with tarfile.open(tar_file_path, 'r') as tar_ref:
            temp_extract_dir = os.path.join(os.path.dirname(tar_file_path), 'temp_extract')
            os.makedirs(temp_extract_dir, exist_ok=True)
            
            try:
                # Adding filter argument to avoid deprecation warning
                tar_ref.extractall(temp_extract_dir, filter=None)
            except tarfile.ReadError:
                corrupted_files.append(tar_file_path)
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                return

            for root, _, files in os.walk(temp_extract_dir):
                if '__MACOSX' in root:
                    continue
                for file in files:
                    if file.startswith('._'):
                        continue
                    if file.endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        target_pdf_path = os.path.join(target_subdir, file)
                        shutil.copy(file_path, target_pdf_path)
                        pdfs_copied.append(os.path.abspath(target_pdf_path))

            shutil.rmtree(temp_extract_dir)

    except Exception as e:
        corrupted_files.append(tar_file_path)
        return

    processing_time = round(time.time() - start_time, 2)
    result = {
        "tar_file": os.path.abspath(tar_file_path),
        "pdfs_copied": pdfs_copied,
        "total_pdfs_copied": len(pdfs_copied),
        "processing_time_seconds": processing_time
    }

    with open(output_jsonl, 'a') as jsonl_file:
        jsonl_file.write(json.dumps(result) + '\n')

    processed_files.append(tar_file_path)
    print(f"Done processing {tar_file_path}")

def process_directory(root_dir, target_dir, output_jsonl):
    """Processes all tar files in a directory."""
    os.makedirs(target_dir, exist_ok=True)

    processed_files = []
    corrupted_files = []

    files = os.listdir(root_dir)

    for tar_file_name in files:
        if re.match(r"arXiv_src_\d+_\d+\.tar$", tar_file_name):  # Updated regex
            tar_file_path = os.path.join(root_dir, tar_file_name)
            process_tar_file(tar_file_path, target_dir, output_jsonl, processed_files, corrupted_files)

    # Final statistics
    print(f"\nProcessing complete. Stats:")
    print(f"Processed .tar files = {len(processed_files)}")
    print(f"Not processed / Corrupted .tar files = {len(corrupted_files)}")
    if corrupted_files:
        print(f"Corrupted .tar files: {', '.join(corrupted_files)}")

if __name__ == "__main__":
    src_dir = "./workingData/eda/"   # Directory containing arXiv_src_x_x.tar files
    target_dir = "./test_data/"      # Directory for extracted PDFs
    output_jsonl = "pdf_copy_results.jsonl"  # Output file for results
    
    process_directory(src_dir, target_dir, output_jsonl)
