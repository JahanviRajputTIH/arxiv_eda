import os
import re
import json
import gzip
import tarfile
import zipfile
import shutil
import time
import io
from collections import defaultdict
from pathlib import Path


# List of extensions associated with LaTeX source files
latex_extensions = ['.tex', '.sty', '.cls', '.bib']

# Common image file extensions
image_extensions = ['.png', '.jpg', '.jpeg', '.pdf', '.eps', '.svg', '.gif', '.ps']

# Files and directories to skip
skip_files = ['__MACOSX', '._']

def remove_comments(content):
    """
    Remove LaTeX comments from the content.
    """
    return re.sub(r"(?<!\\)%.*", "", content)

def parse_tex_file(content):
    """
    Analyzes LaTeX content for figures, tables, and equations.
    Includes all occurrences in the uncommented part of the content.
    """
    content = remove_comments(content)
    
    # Find figures with enhanced pattern matching
    figure_patterns = [
        r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}",  # \includegraphics[options]{file}
        r"\\psfig\{file=([^,]+),",  # \psfig{file=fig1.ps,width=7cm,angle=90}
        r"\\epsfig\{file=([^,]+),",  # \epsfig{file=fig1.ps,width=7cm,angle=90}
        r"\\epsfbox\{([^}]+)\}",  # \epsfbox{fig1.ps}
        r"\\epsfysize=[^ ]+ \\epsfbox\{([^}]+)\}",  # \epsfysize=600pt \epsfbox{fig1.ps}
        r"\\begin\{figure\}.*?\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}",  # \begin{figure}...\includegraphics{file}
        r"\\begin\{figure\}.*?\\psfig\{file=([^,]+),",  # \begin{figure}...\psfig{file=fig1.ps,width=7cm,angle=90}
        r"\\begin\{figure\}.*?\\epsfig\{file=([^,]+),",  # \begin{figure}...\epsfig{file=fig1.ps,width=7cm,angle=90}
        r"\\begin\{figure\}.*?\\epsfbox\{([^}]+)\}",  # \begin{figure}...\epsfbox{fig1.ps}
        r"\\begin\{figure\}.*?\\epsfysize=[^ ]+ \\epsfbox\{([^}]+)\}"  # \begin{figure}...\epsfysize=600pt \epsfbox{fig1.ps}
    ]
    
    # Find all figure occurrences
    figures = []
    for pattern in figure_patterns:
        matches = re.findall(pattern, content, re.DOTALL)
        figures.extend(matches)
    
    # Clean up figure paths
    figures = [f.strip() for f in figures]
    figures = list(set(figures))
    
    # Count all table occurrences
    tables = len(re.findall(r"\\begin\{table\}", content))
    
    # Count all equation occurrences
    equation_patterns = [
        r"\\begin\{equation\}",  # \begin{equation}
        r"\\begin\{equation\*}",  # \begin{equation*}
        r"\\begin\{align\}",  # \begin{align}
        r"\\begin\{align\*}",  # \begin{align*}
        r"\\begin\{multline\}",  # \begin{multline}
        r"\\begin\{multline\*}",  # \begin{multline*}
        r"\\begin\{gather\}",  # \begin{gather}
        r"\\begin\{gather\*}",  # \begin{gather*}
        r"\\\[",  # \[
        r"\$\$",  # $$
        r"\\begin\{cases\}",  # \begin{cases}
        r"\\begin\{matrix\}",  # \begin{matrix}
        r"\\begin\{bmatrix\}",  # \begin{bmatrix}
        r"\\begin\{pmatrix\}",  # \begin{pmatrix}
        r"\\begin\{vmatrix\}",  # \begin{vmatrix}
        r"\\begin\{Bmatrix\}",  # \begin{Bmatrix}
        r"\\begin\{smallmatrix\}",  # \begin{smallmatrix}
        r"\\begin\{array\}",  # \begin{array}
        r"\\boxed\{",  # \boxed{
    ]
    
    equations = 0
    for pattern in equation_patterns:
        equations += len(re.findall(pattern, content))
    
    return {
        "figures": figures,  # All figure occurrences
        "tables": tables,    # All table occurrences
        "equations": equations  # All equation occurrences
    }

def check_tex_columns(content):
    """
    Determines if the LaTeX document uses single or multiple columns.
    """
    if "\\documentclass[twocolumn]" in content or "\\twocolumn" in content:
        return "multi-column"
    return "single-column"

def is_latex_file_by_content(content):
    """
    Check if the content appears to be LaTeX by looking for common LaTeX commands.
    """
    latex_commands = ['\\documentclass', '\\begin{document}', '\\end{document}', '\\usepackage']
    preview = content[:500]
    return any(command in preview for command in latex_commands)

def analyze_latex_content(content):
    """
    Comprehensive analysis of LaTeX content.
    """
    parsed_data = parse_tex_file(content)
    column_format = check_tex_columns(content)
    return {
        **parsed_data,
        "column_format": column_format
    }

def check_missing_figures(figures, archive_files):
    """
    Check which figures are missing from the archive.
    Ensures unique entries for found and missing figures.
    """
    found_figures = set()
    missing_figures = set()
    
    for figure in figures:
        figure_found = False
        figure_base = re.escape(figure)  # Properly escape for regex
        
        for ext in image_extensions:
            pattern = f"{figure_base}({ext})?$"
            
            for archive_file in archive_files:
                if re.search(pattern, archive_file, re.IGNORECASE):
                    found_figures.add(archive_file)
                    figure_found = True
                    break
        
        if not figure_found:
            missing_figures.add(figure)
    
    return list(found_figures), list(missing_figures)

def inspect_gz_file(gz_path):
    """
    Inspects a gzipped file for LaTeX content and analyzes it.
    """
    contains_latex = False
    latex_category = None
    latex_source_found = False
    latex_analysis = defaultdict(list)
    all_archive_files = []

    try:
        with gzip.open(gz_path, 'rb') as gz_file:
            decompressed_data = io.BytesIO(gz_file.read())
            
            if tarfile.is_tarfile(decompressed_data):
                with tarfile.open(fileobj=decompressed_data, mode='r') as tar:
                    all_archive_files = [member.name for member in tar.getmembers() if not member.isdir()]
                    
                    for member in tar.getmembers():
                        if member.isdir() or any(skip in member.name for skip in skip_files):
                            continue
                            
                        try:
                            file = tar.extractfile(member)
                            if file is None:
                                continue
                                
                            file_content = file.read().decode('utf-8', errors='ignore')
                            
                            if any(member.name.endswith(ext) for ext in latex_extensions) or is_latex_file_by_content(file_content):
                                contains_latex = True
                                if member.name.endswith('.tex') or is_latex_file_by_content(file_content):
                                    latex_category = '.tex' if member.name.endswith('.tex') else 'content'
                                    analysis = analyze_latex_content(file_content)
                                    found_figures, missing_figures = check_missing_figures(
                                        analysis['figures'],
                                        all_archive_files
                                    )
                                    latex_analysis['files'].append({
                                        'filename': member.name,
                                        'analysis': analysis,
                                        'found_figures': found_figures,
                                        'missing_figures': missing_figures
                                    })
                                
                        except Exception as e:
                            print(f"Error processing file {member.name} in {gz_path}: {e}")
                            continue

    except Exception as e:
        print(f"Error processing archive {gz_path}: {e}")

    return contains_latex, latex_category, latex_source_found, latex_analysis

def process_tar_file(tar_path):
    """
    Process a tar file, extract its contents, and analyze LaTeX content.
    """
    stats = {
        'total_files': 0,
        'total_gz_files': 0,
        'gz_files_with_figures': 0,
        'gz_files_with_tables': 0,
        'gz_files_with_equations': 0,
        'gz_files_with_single_column': 0,
        'gz_files_with_multi_column': 0,
        'total_figures': 0,
        'total_tables': 0,
        'total_equations': 0,
        'total_missing_figures': 0,
        'total_found_figures': 0,
        'gz_files_missing_figures': 0,
        'gz_files_all_figures_present': 0
    }
    
    detailed_analysis = []
    non_processed_files = []

    try:
        with tarfile.open(tar_path, 'r') as tar:
            for member in tar.getmembers():
                if member.isfile():
                    stats['total_files'] += 1
                    if member.name.endswith('.gz'):
                        stats['total_gz_files'] += 1
                        gz_file = tar.extractfile(member)
                        if gz_file is None:
                            non_processed_files.append(member.name)
                            continue
                        
                        # Create the subdirectory if it doesn't exist
                        gz_dir = os.path.dirname(member.name)
                        if gz_dir:
                            os.makedirs(os.path.join(os.path.dirname(tar_path), gz_dir), exist_ok=True)
                        
                        gz_path = os.path.join(os.path.dirname(tar_path), member.name)
                        with open(gz_path, 'wb') as f:
                            f.write(gz_file.read())
                        
                        contains_latex, latex_category, latex_source_found, latex_analysis = inspect_gz_file(gz_path)
                        
                        if contains_latex:
                            has_figures = False
                            has_tables = False
                            has_equations = False
                            has_missing_figures = False
                            has_single_column = False
                            has_multi_column = False
                            
                            for file_analysis in latex_analysis['files']:
                                analysis = file_analysis['analysis']
                                
                                # Figures
                                figures_count = len(analysis['figures'])
                                if figures_count > 0:
                                    has_figures = True
                                    stats['total_figures'] += figures_count
                                
                                # Tables
                                if analysis['tables'] > 0:
                                    has_tables = True
                                    stats['total_tables'] += analysis['tables']
                                
                                # Equations
                                if analysis['equations'] > 0:
                                    has_equations = True
                                    stats['total_equations'] += analysis['equations']
                                
                                # Column format
                                if analysis['column_format'] == 'single-column':
                                    has_single_column = True
                                else:
                                    has_multi_column = True
                                
                                # Missing figures
                                missing_count = len(file_analysis.get('missing_figures', []))
                                found_count = len(file_analysis.get('found_figures', []))
                                stats['total_missing_figures'] += missing_count
                                stats['total_found_figures'] += found_count
                                
                                if missing_count > 0:
                                    has_missing_figures = True
                            
                            # Update file-level statistics
                            if has_figures:
                                stats['gz_files_with_figures'] += 1
                                if has_missing_figures:
                                    stats['gz_files_missing_figures'] += 1
                                else:
                                    stats['gz_files_all_figures_present'] += 1
                            
                            if has_tables:
                                stats['gz_files_with_tables'] += 1
                            
                            if has_equations:
                                stats['gz_files_with_equations'] += 1
                            
                            if has_single_column:
                                stats['gz_files_with_single_column'] += 1
                            
                            if has_multi_column:
                                stats['gz_files_with_multi_column'] += 1
                            
                            if latex_analysis['files']:
                                detailed_analysis.append({
                                    'file': gz_path,
                                    'analysis': latex_analysis
                                })
                        
                        os.remove(gz_path)
                        # Remove the subdirectory if it was created
                        if gz_dir:
                            shutil.rmtree(os.path.join(os.path.dirname(tar_path), gz_dir))
    
    except tarfile.TarError as e:
        print(f"Error processing tar file {tar_path}: {e}")
        non_processed_files.append(tar_path)
    except Exception as e:
        print(f"Unexpected error processing tar file {tar_path}: {e}")
        non_processed_files.append(tar_path)
    
    return stats, detailed_analysis, non_processed_files

def process_parent_directory(parent_dir):
    """
    Process all tar files in a parent directory and analyze their contents.
    Dynamically dump results into a JSONL file after processing each tar.
    """
    # Ensure the parent directory exists
    if not os.path.exists(parent_dir):
        print(f"Error: Directory {parent_dir} does not exist.")
        return
    
    # Create the output file path
    output_file = os.path.join(parent_dir, "all_tar_analysis.jsonl")
    
    # Ensure the directory for the output file exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    all_non_processed_files = []
    
    # Start the total script timer
    total_script_start_time = time.time()
    
    # Open the JSONL file in append mode
    with open(output_file, 'w') as f:
        for filename in os.listdir(parent_dir):
            if filename.endswith('.tar') and not any(skip in filename for skip in skip_files):
                tar_path = os.path.join(parent_dir, filename)
                print(f"Processing {tar_path}...")
                
                # Start the timer for the current tar file
                tar_start_time = time.time()
                
                # Process the tar file
                stats, detailed_analysis, non_processed_files = process_tar_file(tar_path)
                all_non_processed_files.extend(non_processed_files)
                
                # End the timer for the current tar file
                tar_end_time = time.time()
                tar_processing_time = tar_end_time - tar_start_time
                
                # Write the result to the JSONL file immediately
                result = {
                    'tar_file': os.path.abspath(tar_path),  # Absolute path of the tar file
                    'stats': stats,
                    'detailed_analysis': detailed_analysis,
                    'processing_time_seconds': tar_processing_time
                }
                f.write(json.dumps(result) + '\n')
                f.flush()  # Ensure the result is written to the file immediately
                
                print(f"Done processing {tar_path}. Time taken: {tar_processing_time:.2f} seconds")
    
    # End the total script timer
    total_script_end_time = time.time()
    total_script_time = total_script_end_time - total_script_start_time
    
    print(f"All results saved to {output_file}")
    print(f"Non-processed files (corrupted): {len(all_non_processed_files)}")
    print(f"Non-processed files list: {all_non_processed_files}")
    print(f"Total script running time: {total_script_time:.2f} seconds")

# Example usage
if __name__== "__main__":
    parent_directory = 'workingData/eda'  # Path to directory with tar files
    process_parent_directory(parent_directory)