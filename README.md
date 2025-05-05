# PaperNexus Finder

A comprehensive tool for extracting, organizing, and searching exam paper collections.

## Features

- Extract text from PDF question papers using PyMuPDF
- Create a mirrored directory structure with extracted text files
- Track extraction progress with detailed statistics
- Generate JSON indexes of all papers
- Search papers by subject, unit, year, month, and more
- Full-text search capabilities within extracted content
- Support for parallel processing to speed up extraction

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/papernexus-finder.git
   cd papernexus-finder
   ```

2. Create a virtual environment (optional but recommended):

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Directory Structure

The tool expects the following directory structure:

```
papers/
├── subject1/
│   ├── qp/  (question papers)
│   │   ├── u1/
│   │   │   ├── year/
│   │   │   │   ├── paper1.pdf
│   │   │   │   └── paper2.pdf
│   ├── ms/  (mark schemes)
│   │   ├── u1/
│   │   │   ├── year/
│   │   │   │   ├── markscheme1.pdf
│   │   │   │   └── markscheme2.pdf
│   └── txt/  (created by the tool)
│       ├── u1/
│       │   ├── year/
│       │   │   ├── paper1.txt
│       │   │   └── paper2.txt
└── subject2/
    └── ...
```

## Usage

### 1. Extract Text from Papers

Run the extraction script to process all PDF files and create text versions:

```
python extract_papers.py
```

This will:

- Create a mirrored directory structure in the "txt" folder
- Extract text from all PDFs in the "qp" directory
- Generate JSON indexes in the "paper_index" directory
- Track progress with a detailed log

### 2. Search for Papers

Use the search utility to find specific papers:

```
# List all available subjects
python search_papers.py --list

# Search for papers by subject
python search_papers.py --subject physics

# Search for papers by subject and unit
python search_papers.py --subject mathematics --unit 2

# Search for papers by year and month
python search_papers.py --year 2023 --month January

# Search for papers containing specific text
python search_papers.py --subject chemistry --text "organic compounds"
```

### 3. Full-Text Search

For more powerful text searching capabilities:

```
# Search for specific text across all subjects
python full_text_search.py "carbon dioxide"

# Search in specific subjects only
python full_text_search.py "vectors" --subjects mathematics,physics

# Case-sensitive search
python full_text_search.py "DNA" --case-sensitive

# Adjust context lines around matches
python full_text_search.py "integration" --context 5

# Show more matches per file
python full_text_search.py "equations" --max-matches 5
```

## Tips

1. For large collections, the extraction process may take some time.
2. The text extraction preserves most of the content but complex formatting may be lost.
3. Mathematical equations and symbols may not be extracted perfectly.
4. Use the search tools to quickly find relevant papers.
5. Extracted text files can be used for various analysis purposes.

## License

[Your License Here]
