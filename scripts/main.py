import os
import time
import subprocess
import logging
import sys
from pathlib import Path

# Import all modules
from figureTable import process_parent_directory as process_figure_table
from latexType import process_parent_directory as process_latex_type
from mapping import compare_directories
from pdfPageCount import process_tar_files
from sourcePDFcopy import process_directory as process_source_pdf

# Configure logging to write to both terminal and a file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("out.txt"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Define directories
WORKING_DIR = "../../../"
EDA_DIR = os.path.join(WORKING_DIR, "arxiv_data_s3")
PDF_DIR = os.path.join(WORKING_DIR, "arxiv_s3_pdf")
MAPPED_DIR = "./mapped_data"
TARGET_DIR = "test_data"
OUTPUT_JSONL = "pdf_copy_results.jsonl"
MAPPED_JSONL = "mapped.jsonl"

def main():
    # Start the total processing timer
    total_start_time = time.time()

    # Clear the output file at the start of the script
    with open("out.txt", "w") as outfile:
        outfile.write("")

    try:
        # Create directories if they don't exist
        os.makedirs(EDA_DIR, exist_ok=True)
        os.makedirs(PDF_DIR, exist_ok=True)
        os.makedirs(TARGET_DIR, exist_ok=True)
        os.makedirs(MAPPED_DIR, exist_ok=True)

        # Run figureTable analysis
        logger.info("Running figure table analysis...")
        start_time = time.time()
        process_figure_table(EDA_DIR)
        logger.info(f"figureTable.py processing time: {time.time() - start_time:.2f} seconds")

        # Run LaTeX type analysis
        logger.info("Running LaTeX type analysis...")
        start_time = time.time()
        process_latex_type(EDA_DIR)
        logger.info(f"latexType.py processing time: {time.time() - start_time:.2f} seconds")

        # Run mapping analysis with new parameters
        logger.info("Running mapping analysis...")
        start_time = time.time()
        compare_directories(EDA_DIR, PDF_DIR, MAPPED_DIR, MAPPED_JSONL)
        logger.info(f"mapping.py processing time: {time.time() - start_time:.2f} seconds")

        # Run PDF page count analysis
        logger.info("Running PDF page count analysis...")
        start_time = time.time()
        process_tar_files(PDF_DIR)
        logger.info(f"pdfPageCount.py processing time: {time.time() - start_time:.2f} seconds")

        # Run source PDF copy
        logger.info("Running source PDF copy...")
        start_time = time.time()
        process_source_pdf(EDA_DIR, TARGET_DIR, OUTPUT_JSONL)
        logger.info(f"sourcePDFcopy.py processing time: {time.time() - start_time:.2f} seconds")

    except Exception as e:
        logger.error(f"Error in main processing: {e}")
        raise

    # Calculate total processing time
    total_processing_time = time.time() - total_start_time
    logger.info(f"Total processing time: {total_processing_time:.2f} seconds")

if __name__ == "__main__":
    main()