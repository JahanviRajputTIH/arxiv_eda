# Final Exploratory Data Analysis (EDA) CodeBase

## Project Structure

```
working_dir/
│
├── root_dir/ (finalEDA/)
│   ├── *_src_*.tar
│   │   ├── x.gz
│   │   └── y.gz
│   ├── *_src_*.tar
│   │   ├── x1.gz
│   │   └── y1.gz
│   └── *_src_*.tar
│       ├── x2.gz
│       └── y2.gz
├── target_dir/ (onlyPDF/)
│   ├── *_pdf_*.tar
│   │   ├── x.pdf
│   │   └── y.pdf
│   ├── *_pdf_*.tar
│   │   ├── x1.pdf
│   │   └── y1.pdf
│   └── *_pdf_*.tar
│       ├── x2.pdf
│       └── y2.pdf
│
└── scripts (main.py, etc. in working directory only, not in scripts sub-directory)
```


OR SIMPLY
```
project_root/
├── workingData/
│   ├── arxiv_data_s3/
│   └── arxiv_s3_pdf/
├── test_data/
├── main.py
├── figureTable.py
├── latexType.py
├── mapping.py
├── pdfPageCount.py
└── sourcePDFcopy.py
```

## Scripts and Output Files

### sourcePDFcopy.py (eda5.py) 
- **Output**: `pdf_copy_results.jsonl` made in  Working directory where the script is executed


### latexType.py (eda3_4.py)
- **Outputs**:
  1. `insideZipAnalysisNumbers.jsonl` ( made in root_dir )
  2. `insideZipAnalysis.jsonl`  ( made in root_dir )

### figureTable.py (eda1_2_6.py)
- **Output**: `all_zip_analysis.jsonl` made Inside `root_dir` containing all zips

### pdfPageCount.py (eda8.py)
- **Output**: pdf_page_counts.jsonl made inside working_dir


### mapping.py (eda7.py) 
- **Output**: `mapping.jsonl` made inside working_dir

### main.py 
- Main working engine of code base calling above files' functions

  

### NOTE
- Define root_dir , target_dir and sourcePDFtarget (test_data directory, destination of source PDFs having no source file, required in eda5.py) directory names as the value of these variables of main.py at their respective initialization places
- `gz_extracted` and `pdf_extracted` sub-directories are made inside `working_dir` for `mapping.py` task which can be deleted or left as it is in `working_dir` 

