import os
import json
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print
from fuzzywuzzy import process, fuzz

class PaperSearcher:
    def __init__(self, index_dir="paper_index"):
        self.index_dir = Path(index_dir)
        self.master_index = {}
        self.console = Console()
        
        # Load master index if exists
        master_index_path = self.index_dir / "master_index.json"
        if master_index_path.exists():
            with open(master_index_path, 'r', encoding='utf-8') as f:
                self.master_index = json.load(f)
        else:
            # Load individual subject indexes
            for index_file in self.index_dir.glob("*_index.json"):
                subject = index_file.stem.replace("_index", "")
                with open(index_file, 'r', encoding='utf-8') as f:
                    self.master_index[subject] = json.load(f)
    
    def list_subjects(self):
        """List all available subjects"""
        table = Table(title="Available Subjects")
        table.add_column("Subject", style="cyan")
        table.add_column("QPs", style="green")
        table.add_column("Mark Schemes", style="yellow")
        table.add_column("Text Files", style="blue")
        
        for subject, data in self.master_index.items():
            qp_count = len(data.get("question_papers", []))
            ms_count = len(data.get("mark_schemes", []))
            txt_count = len(data.get("extracted_texts", []))
            table.add_row(subject, str(qp_count), str(ms_count), str(txt_count))
        
        self.console.print(table)
    
    def search_papers(self, subject=None, unit=None, year=None, month=None, code=None, text=None):
        """Search for papers based on criteria"""
        results = []
        
        subjects_to_search = [subject] if subject else self.master_index.keys()
        
        for subj in subjects_to_search:
            if subj not in self.master_index:
                # Try fuzzy matching if exact subject not found
                matches = process.extract(subj, self.master_index.keys(), limit=1)
                if matches and matches[0][1] > 70:  # 70% similarity threshold
                    subj = matches[0][0]
                    print(f"[yellow]Using closest match: {subj}[/yellow]")
                else:
                    continue
                    
            papers = self.master_index[subj].get("question_papers", [])
            
            for paper in papers:
                if unit and paper.get("unit") != unit:
                    continue
                if year and paper.get("year") != year:
                    continue
                if month and paper.get("month") != month:
                    continue
                if code and paper.get("code") != code:
                    continue
                
                # If text search is enabled, search in the text file
                if text:
                    txt_path = None
                    for txt in self.master_index[subj].get("extracted_texts", []):
                        if txt.get("filename") == paper.get("filename").replace(" - QP ", " - TXT ").replace(".pdf", ".txt"):
                            txt_path = txt.get("path")
                            break
                    
                    if txt_path and os.path.exists(txt_path):
                        try:
                            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read().lower()
                                if text.lower() not in content:
                                    continue
                        except Exception as e:
                            print(f"[red]Error reading {txt_path}: {e}[/red]")
                            continue
                
                # Find mark scheme if available
                ms_path = None
                for ms in self.master_index[subj].get("mark_schemes", []):
                    if ms.get("year") == paper.get("year") and ms.get("month") == paper.get("month") and ms.get("unit") == paper.get("unit"):
                        ms_path = ms.get("path")
                        break
                
                # Find text file if available
                txt_path = None
                for txt in self.master_index[subj].get("extracted_texts", []):
                    if txt.get("year") == paper.get("year") and txt.get("month") == paper.get("month") and txt.get("unit") == paper.get("unit"):
                        txt_path = txt.get("path")
                        break
                
                results.append({
                    "subject": subj,
                    "unit": paper.get("unit"),
                    "year": paper.get("year"),
                    "month": paper.get("month"),
                    "code": paper.get("code"),
                    "question_paper": paper.get("path"),
                    "mark_scheme": ms_path,
                    "text_file": txt_path
                })
        
        return results
    
    def display_results(self, results):
        """Display search results in a table"""
        if not results:
            print("[bold red]No matching papers found![/bold red]")
            return
        
        table = Table(title=f"Search Results ({len(results)} papers found)")
        table.add_column("Subject", style="cyan")
        table.add_column("Unit", style="blue")
        table.add_column("Year", style="green")
        table.add_column("Month", style="yellow")
        table.add_column("Code", style="magenta")
        table.add_column("QP", style="green")
        table.add_column("MS", style="yellow")
        table.add_column("TXT", style="blue")
        
        for result in results:
            table.add_row(
                result["subject"],
                result["unit"],
                result["year"],
                result["month"],
                result["code"],
                "✓" if result["question_paper"] else "✗",
                "✓" if result["mark_scheme"] else "✗",
                "✓" if result["text_file"] else "✗"
            )
        
        self.console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Search for exam papers")
    parser.add_argument("--subject", help="Subject name")
    parser.add_argument("--unit", help="Unit number")
    parser.add_argument("--year", help="Year")
    parser.add_argument("--month", help="Month (January, May, October)")
    parser.add_argument("--code", help="Paper code")
    parser.add_argument("--text", help="Search within the text content")
    parser.add_argument("--list", action="store_true", help="List all subjects")
    
    args = parser.parse_args()
    
    searcher = PaperSearcher()
    
    if args.list:
        searcher.list_subjects()
        return
    
    results = searcher.search_papers(
        subject=args.subject,
        unit=args.unit,
        year=args.year,
        month=args.month,
        code=args.code,
        text=args.text
    )
    
    searcher.display_results(results)

if __name__ == "__main__":
    main()