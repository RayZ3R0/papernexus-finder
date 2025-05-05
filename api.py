from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import fitz  # PyMuPDF
import tempfile
from io import BytesIO
from full_text_search import FullTextSearcher

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.json
        
        query = data.get('query', '')
        subjects = data.get('subjects')
        case_sensitive = data.get('caseSensitive', False)
        context_lines = data.get('contextLines', 2)
        
        searcher = FullTextSearcher()
        results = searcher.search_text(
            query=query,
            subjects=subjects,
            case_sensitive=case_sensitive,
            context_lines=context_lines
        )
        
        # Format the results for the UI
        formatted_results = []
        for result in results:
            formatted_results.append({
                'subject': result.get('subject', ''),
                'unit': result.get('unit', ''),
                'year': result.get('year', ''),
                'month': result.get('month', ''),
                'qp_path': result.get('qp_path', ''),
                'ms_path': result.get('ms_path', ''),
                'matches': result.get('matches', []),
                'query': query
            })
        
        return jsonify(formatted_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/files', methods=['GET'])
def get_file():
    path = request.args.get('path', '')
    
    if not path or not os.path.exists(path):
        return "File not found", 404
    
    try:
        return send_file(path)
    except Exception as e:
        return str(e), 500

@app.route('/api/preview', methods=['GET'])
def get_preview():
    """Generate and return a preview image of the page with the first match"""
    path = request.args.get('path', '')
    match_line = request.args.get('line')
    query = request.args.get('query', '')
    
    if not path or not os.path.exists(path):
        return "File not found", 404
    
    try:
        # Open the PDF
        doc = fitz.open(path)
        
        # Determine which page to render
        target_page = 0  # Default to first page
        
        if match_line and query:
            try:
                # Try to find the page that contains the match
                match_line = int(match_line)
                
                # Get the corresponding text file path
                txt_path = path.replace('.pdf', '.txt')
                if '/qp/' in path:
                    # Try replacing the directory structure
                    txt_path = path.replace('/qp/', '/txt/').replace('.pdf', '.txt')
                
                if os.path.exists(txt_path):
                    with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Find all page break markers and their line numbers
                    lines = content.split('\n')
                    page_break_lines = [i for i, line in enumerate(lines) if "--- Page Break ---" in line]
                    page_break_lines = [-1] + page_break_lines + [len(lines)]  # Add start and end markers
                    
                    # Determine which page segment contains our match line
                    for page_num, (start_break, end_break) in enumerate(zip(page_break_lines[:-1], page_break_lines[1:])):
                        # Account for the page break marker itself in line counting
                        adjusted_start = start_break + 1
                        
                        # If the match line is between this page's start and end
                        if adjusted_start <= match_line-1 < end_break:
                            target_page = page_num
                            print(f"Match on page {target_page}, line {match_line}, boundaries: {adjusted_start}-{end_break}")
                            break
                    
                    print(f"Selected target page: {target_page} for match at line {match_line}")
            except Exception as e:
                import traceback
                print(f"Error finding match page: {str(e)}")
                print(traceback.format_exc())
                # Continue with default page 0
        
        # Make sure the target page is valid
        if target_page >= len(doc):
            print(f"Target page {target_page} exceeds document length {len(doc)}, using page 0")
            target_page = 0
        
        # Render the target page
        page = doc.load_page(target_page)
        
        # Render page to an image with higher resolution for better readability
        zoom = 2  # Zoom factor
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PNG image
        img_bytes = BytesIO(pix.tobytes("png"))
        
        # Close the document
        doc.close()
        
        # Return the image
        img_bytes.seek(0)
        return send_file(img_bytes, mimetype='image/png')
    except Exception as e:
        import traceback
        print(f"Preview error: {str(e)}")
        print(traceback.format_exc())
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)