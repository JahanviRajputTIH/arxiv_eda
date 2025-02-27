import os
import gzip
import tarfile
import json
import time
import io
import re
from pathlib import Path


latex_extensions = ['.tex', '.sty', '.cls', '.bib']

def is_latex_file_by_content(content):
    latex_commands = ['\\documentclass', '\\begin{document}', '\\end{document}', '\\usepackage']
    return any(command in content for command in latex_commands)

def inspect_gz_file(gz_file_obj):
    result = {
        'gz_file': gz_file_obj.name,
        'contains_tex': False,
        'contains_content_latex': False,
        'contains_other_latex': False
    }

    try:
        decompressed_data = io.BytesIO(gz_file_obj.read())
        if tarfile.is_tarfile(decompressed_data):
            with tarfile.open(fileobj=decompressed_data, mode='r') as tar:
                for member in tar.getmembers():
                    if member.name.endswith('.tex'):
                        result['contains_tex'] = True
                        break
                    if any(member.name.endswith(ext) for ext in latex_extensions if ext != '.tex'):
                        result['contains_other_latex'] = True
                    file = tar.extractfile(member)
                    if file:
                        file_content = file.read(500).decode('utf-8', errors='ignore')
                        if is_latex_file_by_content(file_content):
                            result['contains_content_latex'] = True
        else:
            content = decompressed_data.read(500).decode('utf-8', errors='ignore')
            if is_latex_file_by_content(content):
                result['contains_content_latex'] = True
    except Exception as e:
        print(f"Error inspecting .gz file {gz_file_obj.name}: {e}")

    return result

def categorize_gz_file(gz_result):
    if gz_result['contains_tex']:
        return 'tex'
    elif gz_result['contains_content_latex']:
        return 'content_latex'
    elif gz_result['contains_other_latex']:
        return 'other_latex'

    return None

def process_tar_archive(tar_path):
    gz_results = []

    try:
        with tarfile.open(tar_path, 'r') as tar_ref:
            gz_files = sorted([tar_info for tar_info in tar_ref.getmembers() 
                             if tar_info.name.endswith('.gz') and 
                             not tar_info.name.startswith('__MACOSX')],
                            key=lambda x: x.name)
            
            for tar_info in gz_files:
                try:
                    with tar_ref.extractfile(tar_info) as gz_file_obj:
                        gz_result = inspect_gz_file(gz_file_obj)
                        gz_results.append(gz_result)
                except Exception as e:
                    print(f"Error processing .gz file {tar_info.name} in {tar_path}: {e}")
    except tarfile.TarError as e:
        print(f"Tar file error for {tar_path}: {e}")
        raise  # Re-raise the exception to be caught outside
    except Exception as e:
        print(f"Error processing tar file {tar_path}: {e}")
        raise  # Re-raise the exception to be caught outside

    return {
        'tar_file': os.path.abspath(tar_path),
        'gz_files': gz_results
    }

def process_parent_directory(parent_dir):
    all_tar_stats = []
    processed_files = []
    corrupted_files = []
    start_time = time.time()
    summary_file = os.path.join(parent_dir, "insideTarAnalysisNumbers.jsonl")
    output_file = os.path.join(parent_dir, "insideTarAnalysis.jsonl")

    with open(summary_file, 'w') as summary_f, open(output_file, 'w') as output_f:
        for filename in os.listdir(parent_dir):
            if filename.endswith('.tar'):  # Change to match tar files directly
                tar_path = os.path.join(parent_dir, filename)
                print(f"Processing {tar_path}...")

                try:
                    archive_results = process_tar_archive(tar_path)
                    tex_count = 0
                    other_latex_count = 0
                    content_latex_count = 0
                    
                    for gz_result in archive_results['gz_files']:
                        category = categorize_gz_file(gz_result)
                        if category == 'tex':
                            tex_count += 1
                        elif category == 'other_latex':
                            other_latex_count += 1
                        elif category == 'content_latex':
                            content_latex_count += 1
                    
                    total_latex = tex_count + other_latex_count + content_latex_count

                    output_f.write(json.dumps(archive_results) + '\n')
                    output_f.flush()

                    tar_stats = {
                        'tar_file': os.path.abspath(tar_path),
                        'total_gz_files': len(archive_results['gz_files']),
                        'gz_files_with_latex': total_latex,
                        'gz_files_with_tex': tex_count,
                        'gz_files_with_content_latex': content_latex_count,
                        'gz_files_with_other_latex': other_latex_count,
                        'processing_time': round(time.time() - start_time, 2)
                    }
                    all_tar_stats.append(tar_stats)

                    summary_f.write(json.dumps(tar_stats) + '\n')
                    summary_f.flush()

                    print(f"Done processing {tar_path}")
                    processed_files.append(tar_path)

                except Exception as e:
                    print(f"Error processing tar file {tar_path}: {e}")
                    corrupted_files.append(tar_path)

    # Print Stats
    print(f"\nProcessing complete. Stats:")
    print(f"Processed .tar files = {len(processed_files)}")
    print(f"Not processed / Corrupted .tar files = {len(corrupted_files)}")
    if corrupted_files:
        print(f"Corrupted .tar files: {', '.join(corrupted_files)}")

    print(f"Summary saved to {summary_file}")
    print(f"All results saved to {output_file}")

if __name__ == "__main__":
    # Test case with source directory
    src_dir = "workingData/eda/"  # Directory containing x_src_y.tar files
    process_parent_directory(src_dir)
