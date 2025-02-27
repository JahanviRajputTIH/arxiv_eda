import os
import tarfile
import json
import shutil
import time
from pathlib import Path
import re

def extract_tar(tar_path, extract_to, file_ext):
    """Extract files from TAR archive."""
    extracted_files = set()
    Path(extract_to).mkdir(parents=True, exist_ok=True)
    
    try:
        with tarfile.open(tar_path, 'r') as tar:
            for member in tar.getmembers():
                if (member.name.lower().endswith(file_ext) and 
                    "__MACOSX" not in member.name):
                    member = tar.getmember(member.name)
                    tar.extract(member, extract_to, filter='data')
                    base_name = os.path.splitext(os.path.basename(member.name))[0]
                    extracted_files.add((base_name, member.name))
    except tarfile.ReadError:
        print(f"Error: Unable to read tar file {tar_path}")
        return None
    return extracted_files

def parse_filename(filename):
    """Parse filename to extract values from pattern arXiv_[src/pdf]_XXXX_YYY.tar"""
    pattern = r"arXiv_(src|pdf)_(\d+)_(\d+)\.tar"
    match = re.match(pattern, filename)
    if match:
        file_type, x, y = match.groups()
        return x, y, file_type
    return None

def create_mapped_directory(src_files, pdf_files, mapped_dir, tar_pair_name, src_extract_dir, pdf_extract_dir):
    """Create directory with mapped files and return mapping information."""
    mapped_files = []
    tar_dir = os.path.join(mapped_dir, tar_pair_name)
    os.makedirs(tar_dir, exist_ok=True)

    # Create set of base names for quick lookup
    src_dict = {base: full_path for base, full_path in src_files}
    pdf_dict = {base: full_path for base, full_path in pdf_files}

    # Find common base names
    common_bases = set(src_dict.keys()) & set(pdf_dict.keys())

    for base in common_bases:
        # Create subdirectory for each mapped pair
        base_dir = os.path.join(tar_dir, base)
        os.makedirs(base_dir, exist_ok=True)

        # Copy source file
        src_path = os.path.join(src_extract_dir, src_dict[base])
        dst_src_path = os.path.join(base_dir, f"{base}.gz")
        shutil.copy2(src_path, dst_src_path)

        # Copy PDF file
        pdf_path = os.path.join(pdf_extract_dir, pdf_dict[base])
        dst_pdf_path = os.path.join(base_dir, f"{base}.pdf")
        shutil.copy2(pdf_path, dst_pdf_path)

        mapped_files.append({
            "base_name": base,
            "directory": base_dir,
            "source_file": dst_src_path,
            "pdf_file": dst_pdf_path
        })

    return mapped_files

def process_tar_pair(src_tar_path, pdf_tar_path, mapping_file, mapped_file, pair_name, 
                    src_dir, pdf_dir, src_file_name, pdf_file_name, mapped_dir):
    """Process a pair of TAR files and create mapped directory structure."""
    start_time = time.time()

    # Extract files from both archives
    src_extract_dir = f"./gz_extracted/{pair_name}"
    pdf_extract_dir = f"./pdf_extracted/{pair_name}"
    
    gz_files = extract_tar(src_tar_path, src_extract_dir, ".gz")
    pdf_files = extract_tar(pdf_tar_path, pdf_extract_dir, ".pdf")

    # If either tar file is corrupted, consider it unpaired
    if gz_files is None or pdf_files is None:
        shutil.rmtree(src_extract_dir, ignore_errors=True)
        shutil.rmtree(pdf_extract_dir, ignore_errors=True)
        return None

    # Create sets of base names for traditional mapping analysis
    gz_bases = {base for base, _ in gz_files}
    pdf_bases = {base for base, _ in pdf_files}

    # Find mismatches for mapping.jsonl
    missing_gz = pdf_bases - gz_bases
    missing_pdf = gz_bases - pdf_bases

    # Write to mapping.jsonl
    for base in missing_gz:
        mapping_file.write(json.dumps({
            "path": f"{pdf_dir}/{pdf_file_name}/{base}.pdf",
            "status": "Missing .gz"
        }) + '\n')
        
    for base in missing_pdf:
        mapping_file.write(json.dumps({
            "path": f"{src_dir}/{src_file_name}/{base}.gz",
            "status": "Missing .pdf"
        }) + '\n')

    # Create mapped directory structure and get mapping information
    mapped_files = create_mapped_directory(gz_files, pdf_files, mapped_dir, pair_name, 
                                         src_extract_dir, pdf_extract_dir)

    # Calculate processing time
    processing_time = time.time() - start_time

    # Write to mapped.jsonl
    mapped_entry = {
        "tar_pair": pair_name,
        "mapped_directory": os.path.join(mapped_dir, pair_name),
        "total_mapped_files": len(mapped_files),
        "mapped_files": mapped_files,
        "processing_time_seconds": round(processing_time, 2),
        "source_tar": src_file_name,
        "pdf_tar": pdf_file_name
    }
    mapped_file.write(json.dumps(mapped_entry) + '\n')

    # Cleanup temporary extraction directories
    shutil.rmtree(src_extract_dir, ignore_errors=True)
    shutil.rmtree(pdf_extract_dir, ignore_errors=True)

    return {
        "pair_name": pair_name,
        "total_gz": len(gz_bases),
        "total_pdf": len(pdf_bases),
        "mapped": len(gz_bases & pdf_bases),
        "missing_gz": len(missing_gz),
        "missing_pdf": len(missing_pdf)
    }

def compare_directories(src_dir, pdf_dir, mapped_dir="./mapped_data", mapped_jsonl="mapped.jsonl"):
    """Compare TAR files and create mapped directory structure."""
    total_stats = []    
    unpaired_files = []
    
    # Create mapped directory
    os.makedirs(mapped_dir, exist_ok=True)

    # Get lists of files
    src_files = [f for f in os.listdir(src_dir) if f.endswith('.tar')]
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.tar')]

    # Create mapping based on x and y values
    src_mapping = {}
    pdf_mapping = {}

    for src_file in src_files:
        parsed = parse_filename(src_file)
        if parsed:
            x, y, _ = parsed
            src_mapping[(x, y)] = src_file

    for pdf_file in pdf_files:
        parsed = parse_filename(pdf_file)
        if parsed:
            x, y, _ = parsed
            pdf_mapping[(x, y)] = pdf_file

    # Find matching pairs
    matching_pairs = set(src_mapping.keys()) & set(pdf_mapping.keys())
    
    current_dir = Path(os.getcwd())
    mapping_path = current_dir / "mapping.jsonl"
    mapped_path = current_dir / mapped_jsonl

    with mapping_path.open('w') as mapping_file, mapped_path.open('w') as mapped_file:
        # Process matching pairs
        for x, y in matching_pairs:
            src_file = src_mapping[(x, y)]
            pdf_file = pdf_mapping[(x, y)]
            pair_name = f"{x}_{y}"
            
            stats = process_tar_pair(
                os.path.join(src_dir, src_file),
                os.path.join(pdf_dir, pdf_file),
                mapping_file,
                mapped_file,
                pair_name,
                src_dir,
                pdf_dir,
                src_file,
                pdf_file,
                mapped_dir
            )
            
            if stats is None:
                unpaired_files.append(f"Corrupted file in pair: {src_file} or {pdf_file}")
            else:
                total_stats.append(stats)

    # Find and record unpaired files
    for src_file in src_files:
        parsed = parse_filename(src_file)
        if parsed:
            x, y, _ = parsed
            if (x, y) not in pdf_mapping:
                unpaired_files.append(f"Missing PDF counterpart for source file: {src_file}")
    
    for pdf_file in pdf_files:
        parsed = parse_filename(pdf_file)
        if parsed:
            x, y, _ = parsed
            if (x, y) not in src_mapping:
                unpaired_files.append(f"Missing source counterpart for PDF file: {pdf_file}")

    # Generate and print summary report
    summary = {
        "total_pairs": len(total_stats),
        "total_gz": sum(s['total_gz'] for s in total_stats),
        "total_pdf": sum(s['total_pdf'] for s in total_stats),
        "total_mapped": sum(s['mapped'] for s in total_stats),
        "total_missing_gz": sum(s['missing_gz'] for s in total_stats),
        "total_missing_pdf": sum(s['missing_pdf'] for s in total_stats),
        "unpaired_files": unpaired_files
    }

    print(f"\nSummary Report:")
    print(f"Processed {summary['total_pairs']} file pairs")
    print(f"Total .gz files: {summary['total_gz']}")
    print(f"Total .pdf files: {summary['total_pdf']}")
    print(f"Perfect mappings: {summary['total_mapped']}")
    print(f"Missing .gz files: {summary['total_missing_gz']}")
    print(f"Missing .pdf files: {summary['total_missing_pdf']}")
    print(f"\nUnpaired .tar files: {len(unpaired_files)}")
    for msg in unpaired_files:
        print(f" - {msg}")

if __name__ == "__main__":
    compare_directories(
        src_dir="workingData/eda",
        pdf_dir="workingData/pdf"
    )