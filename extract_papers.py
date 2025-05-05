import os
import json
import fitz  # PyMuPDF
import re
import shutil
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("extraction_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PaperNexusExtractor:
    def __init__(self, base_dir="papers"):
        self.base_dir = Path(base_dir)
        self.subjects = [d for d in os.listdir(self.base_dir) 
                        if os.path.isdir(os.path.join(self.base_dir, d))]
        self.stats = {
            "total_papers": 0,
            "extracted_papers": 0,
            "failed_papers": 0,
            "subjects_processed": 0
        }
        self.papers_index = {}
        self.output_dir = Path("paper_index")
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file using PyMuPDF with improved layout handling"""
        try:
            doc = fitz.open(pdf_path)
            text = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Extract text with better layout preservation
                text.append(page.get_text("text"))
            
            # Join all pages with page separators for better navigation
            full_text = "\n\n--- Page Break ---\n\n".join(text)
            doc.close()
            
            return full_text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return None
    
    def create_directory_structure(self):
        """Create txt directories next to qp and ms directories"""
        for subject in self.subjects:
            subject_path = self.base_dir / subject
            txt_dir = subject_path / "txt"
            
            # Create txt directory if it doesn't exist
            if not txt_dir.exists():
                txt_dir.mkdir(exist_ok=True)
                logger.info(f"Created txt directory for {subject}")
            
            # Create unit subdirectories
            if (subject_path / "qp").exists():
                for unit_dir in (subject_path / "qp").iterdir():
                    if unit_dir.is_dir():
                        unit_txt_dir = txt_dir / unit_dir.name
                        unit_txt_dir.mkdir(exist_ok=True)
                        
                        # Create year subdirectories
                        for year_dir in unit_dir.iterdir():
                            if year_dir.is_dir():
                                year_txt_dir = unit_txt_dir / year_dir.name
                                year_txt_dir.mkdir(exist_ok=True)
    
    def process_pdf(self, pdf_path, txt_path):
        """Process a single PDF file and save its text"""
        try:
            text = self.extract_text_from_pdf(pdf_path)
            if text:
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.stats["extracted_papers"] += 1
                return True
            else:
                self.stats["failed_papers"] += 1
                return False
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {str(e)}")
            self.stats["failed_papers"] += 1
            return False
            
    def process_subject(self, subject):
        """Process all PDFs in a subject's qp directory with parallel processing"""
        subject_path = self.base_dir / subject
        qp_path = subject_path / "qp"
        subject_index = {
            "question_papers": [],
            "mark_schemes": [],
            "extracted_texts": []
        }
        
        if not qp_path.exists():
            logger.warning(f"QP directory not found for {subject}")
            return subject_index
        
        # Find all PDF files in qp directory recursively
        pdf_files = []
        pdf_txt_pairs = []
        
        for root, _, files in os.walk(qp_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_path = os.path.join(root, file)
                    
                    # Determine the corresponding text file path
                    rel_path = os.path.relpath(pdf_path, qp_path)
                    txt_path = subject_path / "txt" / rel_path
                    txt_path = txt_path.with_suffix('.txt')
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(txt_path), exist_ok=True)
                    
                    pdf_files.append(pdf_path)
                    
                    # Process the PDF if text file doesn't exist or is older
                    if not txt_path.exists() or os.path.getmtime(pdf_path) > os.path.getmtime(txt_path):
                        pdf_txt_pairs.append((pdf_path, str(txt_path)))
        
        # Keep track of successful extractions for this subject
        successful_extractions = 0
        failed_extractions = 0
        
        # Process files in parallel
        if pdf_txt_pairs:
            # Determine optimal number of workers based on CPU count (but limit to avoid excessive memory usage)
            max_workers = min(os.cpu_count(), 4)  
            
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self.process_pdf_parallel, pdf_path, txt_path) 
                          for pdf_path, txt_path in pdf_txt_pairs]
                
                # Show progress bar
                with tqdm(total=len(futures), desc=f"Processing {subject}") as pbar:
                    for future in as_completed(futures):
                        pdf_path, success = future.result()
                        if success:
                            successful_extractions += 1
                        else:
                            failed_extractions += 1
                        pbar.update(1)
        
        # Update statistics atomically
        self.stats["total_papers"] += len(pdf_files)
        self.stats["extracted_papers"] += successful_extractions
        self.stats["failed_papers"] += failed_extractions
        
        # Build index after extraction
        for pdf_path in pdf_files:
            rel_path = os.path.relpath(pdf_path, qp_path)
            txt_path = subject_path / "txt" / rel_path
            txt_path = txt_path.with_suffix('.txt')
            
            # Add to index
            qp_info = self.parse_filename(os.path.basename(pdf_path))
            qp_info["path"] = str(pdf_path)
            subject_index["question_papers"].append(qp_info)
            
            # Find corresponding mark scheme
            ms_path = self.find_mark_scheme(pdf_path)
            if ms_path:
                ms_info = self.parse_filename(os.path.basename(ms_path))
                ms_info["path"] = str(ms_path)
                subject_index["mark_schemes"].append(ms_info)
            
            # Add extracted text info
            if txt_path.exists():
                txt_info = qp_info.copy()
                txt_info["path"] = str(txt_path)
                subject_index["extracted_texts"].append(txt_info)
        
        # Save subject index
        with open(self.output_dir / f"{subject}_index.json", 'w', encoding='utf-8') as f:
            json.dump(subject_index, f, indent=2)
            
        self.papers_index[subject] = subject_index
        self.stats["subjects_processed"] += 1
        return subject_index
    
    def process_pdf_parallel(self, pdf_path, txt_path):
        """Process a single PDF file and save its text (for parallel execution)"""
        try:
            text = self.extract_text_from_pdf(pdf_path)
            if text:
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                return (pdf_path, True)
            else:
                return (pdf_path, False)
        except Exception as e:
            logger.error(f"Failed to process {pdf_path}: {str(e)}")
            return (pdf_path, False)
    
    def find_mark_scheme(self, qp_path):
        """
        Find corresponding mark scheme for a question paper
        
        Handles various naming patterns for mark schemes across different subjects:
        - Mathematics PURE1 → Mathematics PURE1
        - Chemistry Unit 1 → Chemistry Unit 1
        - FP1 → FP1
        - Standard patterns and special cases like Reserve/Withdrawn
        """
        qp_path = str(qp_path)
        possible_ms_paths = []
        
        # Get directory and filename
        base_dir = os.path.dirname(qp_path)
        filename = os.path.basename(qp_path)
        ms_dir = base_dir.replace("/qp/", "/ms/")
        
        # Create possible MS filenames with different replacement patterns
        
        # 1. Standard pattern: replace QP with MS
        ms_filename1 = filename.replace(" - QP ", " - MS ")
        possible_ms_paths.append(os.path.join(ms_dir, ms_filename1))
        
        # 2. Replace only QP → MS without spaces
        ms_filename2 = filename.replace("QP", "MS")
        possible_ms_paths.append(os.path.join(ms_dir, ms_filename2))
        
        # 3. For files with code in parentheses, try variants with M suffix
        code_match = re.search(r'\((W?\w+\d+(?:_[RW])?)\)', filename)
        if code_match:
            code = code_match.group(1)
            # Some codes change between QP and MS (e.g., WCH11 to WCH11M)
            ms_code = code + "M"
            ms_filename3 = filename.replace(f"({code})", f"({ms_code})")
            ms_filename3 = ms_filename3.replace(" - QP ", " - MS ")
            possible_ms_paths.append(os.path.join(ms_dir, ms_filename3))
        
        # 4. Handle special cases for mathematics-style papers
        # Extract the unit part for more targeted replacements
        unit_match = re.search(r'(PURE|FP|MECH|STATS|D)(\d+)|Unit\s+(\d+)', filename)
        if unit_match:
            # Directory structure might have unit subdirectories
            unit_parts = unit_match.groups()
            unit_type = unit_parts[0] if unit_parts[0] else None
            unit_num = unit_parts[1] if unit_parts[1] else unit_parts[2]
            
            # For cases where the unit directory structure varies
            if unit_type and unit_num:
                # Try alternative directory paths
                alt_dir = base_dir
                possible_unit_paths = [
                    f"{unit_type.lower()}{unit_num}",
                    f"{unit_type}{unit_num}",
                    f"u{unit_num}"
                ]
                
                for unit_path in possible_unit_paths:
                    if f"/qp/{unit_path}/" in alt_dir:
                        alt_ms_dir = alt_dir.replace(f"/qp/{unit_path}/", f"/ms/{unit_path}/")
                        possible_ms_paths.append(os.path.join(alt_ms_dir, ms_filename1))
                        possible_ms_paths.append(os.path.join(alt_ms_dir, ms_filename2))
        
        # 5. For chemistry style papers with u1, u2, etc. directories
        unit_dir_match = re.search(r'/qp/(u\d+)/', qp_path)
        if unit_dir_match:
            unit_dir = unit_dir_match.group(1)
            alt_path = qp_path.replace(f"/qp/{unit_dir}/", f"/ms/{unit_dir}/")
            alt_path = alt_path.replace(" - QP ", " - MS ")
            possible_ms_paths.append(alt_path)
        
        # 6. For IAL papers, ensure we check both IAL and non-IAL versions
        if "(IAL)" in filename:
            non_ial_filename = filename.replace(" (IAL)", "")
            possible_ms_paths.append(os.path.join(ms_dir, non_ial_filename.replace(" - QP ", " - MS ")))
        else:
            # Add IAL version if original is non-IAL
            ial_insertion_point = filename.find(" - ")
            if ial_insertion_point > 0:
                ial_filename = filename[:ial_insertion_point] + " (IAL)" + filename[ial_insertion_point:]
                possible_ms_paths.append(os.path.join(ms_dir, ial_filename.replace(" - QP ", " - MS ")))
        
        # Check all possible paths and return the first one that exists
        for path in possible_ms_paths:
            if os.path.exists(path):
                return path
        
        # If no direct match is found, try a looser match based on unit and year
        if "QP" in filename and (year_match := re.search(r'(\d{4})', filename)):
            year = year_match.group(1)
            ms_dir_contents = []
            
            # Only try listing the directory if it exists
            if os.path.exists(ms_dir):
                try:
                    ms_dir_contents = os.listdir(ms_dir)
                except:
                    pass
                    
            for ms_file in ms_dir_contents:
                # Check if it's a mark scheme with the same year
                if "MS" in ms_file and year in ms_file:
                    # Further check if unit info matches
                    unit_match_qp = re.search(r'(PURE|FP|MECH|STATS|D)(\d+)|Unit\s+(\d+)', filename)
                    unit_match_ms = re.search(r'(PURE|FP|MECH|STATS|D)(\d+)|Unit\s+(\d+)', ms_file)
                    
                    if unit_match_qp and unit_match_ms:
                        # Extract unit information
                        qp_parts = unit_match_qp.groups()
                        ms_parts = unit_match_ms.groups()
                        
                        # Compare unit number
                        qp_unit = qp_parts[1] if qp_parts[1] else qp_parts[2]  
                        ms_unit = ms_parts[1] if ms_parts[1] else ms_parts[2]
                        
                        if qp_unit == ms_unit:
                            # Additionally check month if present
                            month_match_qp = re.search(r'(January|May|June|October)', filename)
                            month_match_ms = re.search(r'(January|May|June|October)', ms_file)
                            
                            if month_match_qp and month_match_ms and month_match_qp.group(1) == month_match_ms.group(1):
                                return os.path.join(ms_dir, ms_file)
        
        # No mark scheme found
        return None
    
    def parse_filename(self, filename):
        """
        Parse information from a filename with multiple pattern support
        
        Handles patterns like:
        - 'Accounting Unit 1 (IAL) - January 2024 - QP (WAC11).pdf'
        - 'Mathematics PURE1 - January 2005 - QP (6663).pdf'
        - 'Mathematics FP1 - May 2013 (Withdrawn) - QP (6667_W).pdf'
        - 'Chemistry Unit 3 (IAL) - January 2013 (Withdrawn) - QP (WCH03).pdf'
        - 'Mathematics MECH1 - January 2001 - QP (6677).pdf'
        - 'Mathematics STATS1 - May 2013 (Reserve) - QP (6683_R).pdf'
        """
        # Basic information to extract
        info = {"filename": filename}
        
        # Extract subject (first word in the filename)
        subject_match = re.search(r'^(\w+)', filename)
        if subject_match:
            info["subject"] = subject_match.group(1)
        
        # Extract year
        year_match = re.search(r'(\d{4})', filename)
        if year_match:
            info["year"] = year_match.group(1)
        
        # Extract month (January, May, June, October, Specimen)
        month_match = re.search(r'(January|May|June|October|Specimen)', filename)
        if month_match:
            info["month"] = month_match.group(1)
        
        # Extract paper type (QP, MS)
        paper_type_match = re.search(r'\s+-\s+(QP|MS)\s+', filename)
        if paper_type_match:
            info["paper_type"] = paper_type_match.group(1)
        
        # Extract code in parentheses at the end
        code_match = re.search(r'\(([^)]+)\)\.pdf$', filename)
        if code_match:
            code = code_match.group(1)
            info["code"] = code
            
            # Extract additional information from code
            # Check if it's a reserve or withdrawn paper
            if code.endswith('_R'):
                info["status"] = "Reserve"
            elif code.endswith('_W'):
                info["status"] = "Withdrawn"
                
        # Check for IAL designation
        if "(IAL)" in filename:
            info["exam_board"] = "IAL"
        
        # Check for special statuses in the filename
        if "(Withdrawn)" in filename and "status" not in info:
            info["status"] = "Withdrawn"
        elif "(Reserve)" in filename and "status" not in info:
            info["status"] = "Reserve"
        
        # Try to extract unit information - different patterns
        
        # Pattern 1: "Unit N" (like "Chemistry Unit 2")
        unit_match = re.search(r'Unit\s+(\d+)', filename)
        if unit_match:
            info["unit"] = unit_match.group(1)
        else:
            # Pattern 2: Specialized subject units (PURE1, FP1, MECH1, STATS1, D1)
            # Look for these patterns specifically
            special_unit_match = None
            
            # Try PURE1, PURE2, etc.
            pure_match = re.search(r'PURE(\d+)', filename)
            if pure_match:
                info["unit_type"] = "PURE"
                info["unit"] = pure_match.group(1)
                special_unit_match = True
                
            # Try FP1, FP2, etc.
            if not special_unit_match:
                fp_match = re.search(r'FP(\d+)', filename)
                if fp_match:
                    info["unit_type"] = "FP"
                    info["unit"] = fp_match.group(1)
                    special_unit_match = True
                    
            # Try MECH1, MECH2, etc.
            if not special_unit_match:
                mech_match = re.search(r'MECH(\d+)', filename)
                if mech_match:
                    info["unit_type"] = "MECH"
                    info["unit"] = mech_match.group(1)
                    special_unit_match = True
                    
            # Try STATS1, STATS2, etc.
            if not special_unit_match:
                stats_match = re.search(r'STATS(\d+)', filename)
                if stats_match:
                    info["unit_type"] = "STATS"
                    info["unit"] = stats_match.group(1)
                    special_unit_match = True
                    
            # Try D1, D2, etc. (Decision)
            if not special_unit_match:
                decision_match = re.search(r'Decision\s+(\d+)', filename)
                if decision_match:
                    info["unit_type"] = "D"
                    info["unit"] = decision_match.group(1)
                    special_unit_match = True
                else:
                    d_match = re.search(r'\sD(\d+)', filename)
                    if d_match:
                        info["unit_type"] = "D"
                        info["unit"] = d_match.group(1)
                        special_unit_match = True
                        
            # If still no match, try to extract unit from the code
            if not special_unit_match:
                # Extract from codes like WCH01, WMA11, 6CH01
                code_unit_match = re.search(r'[W6](?:\w{2})(\d{2})', filename)
                if code_unit_match:
                    unit_num = code_unit_match.group(1)
                    # Convert "01" to "1", "02" to "2", etc.
                    info["unit"] = str(int(unit_num))
                    
        # If we still don't have a unit, check the directory structure
        if "unit" not in info and "/" in filename:
            # Try to extract from directory path for chemistry style /u1/ folders
            u_dir_match = re.search(r'/u(\d+)/', filename)
            if u_dir_match:
                info["unit"] = u_dir_match.group(1)
        
        return info
    
    def generate_master_index(self):
        """Generate a master index of all papers"""
        with open(self.output_dir / "master_index.json", 'w', encoding='utf-8') as f:
            json.dump(self.papers_index, f, indent=2)
            
    def run(self):
        """Run the extraction process with error handling for individual subjects"""
        start_time = time.time()
        logger.info("Starting PaperNexus Extractor")
        logger.info(f"Found subjects: {', '.join(self.subjects)}")
        
        # Create directory structure
        logger.info("Creating directory structure...")
        self.create_directory_structure()
        
        # Process each subject with error handling
        for subject in self.subjects:
            try:
                logger.info(f"Processing subject: {subject}")
                self.process_subject(subject)
            except Exception as e:
                logger.error(f"Error processing subject {subject}: {str(e)}")
                logger.error("Continuing with next subject...")
        
        # Generate master index
        self.generate_master_index()
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Log statistics
        logger.info(f"Extraction complete. Statistics:")
        logger.info(f"Total papers: {self.stats['total_papers']}")
        logger.info(f"Successfully extracted: {self.stats['extracted_papers']}")
        logger.info(f"Failed extractions: {self.stats['failed_papers']}")
        logger.info(f"Subjects processed: {self.stats['subjects_processed']}")
        logger.info(f"Total time: {int(hours)}h {int(minutes)}m {int(seconds)}s")

if __name__ == "__main__":
    extractor = PaperNexusExtractor()
    extractor.run()