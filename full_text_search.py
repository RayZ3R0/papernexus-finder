import os
import json
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
import re

class FullTextSearcher:
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
    
    def search_text(self, query, subjects=None, case_sensitive=False, context_lines=2):
        """Search for text in extracted files"""
        results = []
        
        subjects_to_search = subjects if subjects else self.master_index.keys()
        
        # Convert query to lowercase if not case sensitive
        search_query = query if case_sensitive else query.lower()
        
        for subject in subjects_to_search:
            if subject not in self.master_index:
                continue
                
            extracted_texts = self.master_index[subject].get("extracted_texts", [])
            
            for text_file in extracted_texts:
                txt_path = text_file.get("path")
                
                if not txt_path or not os.path.exists(txt_path):
                    continue
                
                try:
                    with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    # Convert content to lowercase if not case sensitive
                    search_content = content if case_sensitive else content.lower()
                    
                    # Find all occurrences of the query
                    matches = []
                    lines = search_content.split('\n')
                    for i, line in enumerate(lines):
                        if search_query in line:
                            # Get context lines
                            start = max(0, i - context_lines)
                            end = min(len(lines), i + context_lines + 1)
                            
                            # Extract the context
                            context = "\n".join(lines[start:end])
                            match_position = f"Line {i+1}"
                            
                            matches.append({
                                "line": i + 1,
                                "context": context,
                                "original_context": "\n".join(content.split('\n')[start:end])
                            })
                    
                    if matches:
                        results.append({
                            "subject": subject,
                            "unit": text_file.get("unit"),
                            "year": text_file.get("year"),
                            "month": text_file.get("month"),
                            "text_path": txt_path,
                            "matches": matches,
                            # Find corresponding QP and MS
                            "qp_path": self.find_corresponding_file(subject, text_file, "question_papers"),
                            "ms_path": self.find_corresponding_file(subject, text_file, "mark_schemes")
                        })
                
                except Exception as e:
                    print(f"[red]Error reading {txt_path}: {e}[/red]")
        
        return results
    
    def find_corresponding_file(self, subject, text_file, file_type):
        """Find corresponding question paper or mark scheme for a text file"""
        files = self.master_index[subject].get(file_type, [])
        
        for file in files:
            if (file.get("year") == text_file.get("year") and
                file.get("month") == text_file.get("month") and
                file.get("unit") == text_file.get("unit")):
                return file.get("path")
        
        return None
    
    def display_results(self, results, query, max_matches=3):
        """Display search results with context"""
        if not results:
            print("[bold red]No matches found![/bold red]")
            return
        
        total_matches = sum(len(result["matches"]) for result in results)
        print(f"[bold green]Found {total_matches} matches in {len(results)} files[/bold green]")
        
        for result in results:
            # Create header with file info
            header = f"{result['subject']} Unit {result['unit']} - {result['month']} {result['year']}"
            
            # Display file info
            self.console.print(Panel(
                Text(header, style="bold cyan"),
                subtitle=f"[{len(result['matches'])} matches]"
            ))
            
            # Show file paths
            if result["qp_path"]:
                print(f"[green]Question Paper:[/green] {result['qp_path']}")
            if result["ms_path"]:
                print(f"[yellow]Mark Scheme:[/yellow] {result['ms_path']}")
            print(f"[blue]Text File:[/blue] {result['text_path']}")
            
            # Show matches (limited to max_matches)
            match_count = min(len(result["matches"]), max_matches)
            for i in range(match_count):
                match = result["matches"][i]
                
                # Highlight the query in the context
                highlighted_context = re.sub(
                    f"({re.escape(query)})",
                    "[bold yellow]\\1[/bold yellow]",
                    match["original_context"],
                    flags=re.IGNORECASE
                )
                
                self.console.print(Panel(
                    highlighted_context,
                    title=f"Match {i+1}/{len(result['matches'])} - Line {match['line']}",
                    border_style="blue"
                ))
            
            if len(result["matches"]) > max_matches:
                print(f"[dim](and {len(result['matches']) - max_matches} more matches...)[/dim]")
            
            print()

def main():
    parser = argparse.ArgumentParser(description="Full-text search in extracted papers")
    parser.add_argument("query", help="Text to search for")
    parser.add_argument("--subjects", help="Comma-separated list of subjects to search")
    parser.add_argument("--case-sensitive", action="store_true", help="Make search case-sensitive")
    parser.add_argument("--context", type=int, default=2, help="Number of context lines (default: 2)")
    parser.add_argument("--max-matches", type=int, default=3, help="Maximum matches to display per file (default: 3)")
    
    args = parser.parse_args()
    
    searcher = FullTextSearcher()
    
    subjects = args.subjects.split(",") if args.subjects else None
    
    results = searcher.search_text(
        query=args.query,
        subjects=subjects,
        case_sensitive=args.case_sensitive,
        context_lines=args.context
    )
    
    searcher.display_results(results, args.query, args.max_matches)

if __name__ == "__main__":
    main()