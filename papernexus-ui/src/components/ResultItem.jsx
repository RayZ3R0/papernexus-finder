import { useState, useEffect } from 'preact/hooks';
import { File, FileText, RefreshCw, Search, X, ChevronUp, ChevronDown, Eye } from 'preact-feather';

function ResultItem({ result }) {
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isMatchPage, setIsMatchPage] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [previewError, setPreviewError] = useState(false);
  const [showMatchModal, setShowMatchModal] = useState(false);
  const [showMatchPreview, setShowMatchPreview] = useState(false);
  const [activeMatchIndex, setActiveMatchIndex] = useState(0);
  
  // Create a unique ID for this result item
  const itemId = `paper-${result.subject}-${result.year}-${result.month}-${result.unit || 'nounit'}`;
  
  // Load the preview for the result
  const loadPreview = (useFirstMatch = true) => {
    setIsLoading(true);
    setPreviewError(false);
    
    if (result.qp_path && result.matches && result.matches.length > 0) {
      let url = `/api/preview?path=${encodeURIComponent(result.qp_path)}`;
      
      // Add match line info if we want to show the match page
      if (useFirstMatch) {
        const firstMatchLine = result.matches[0].line;
        url += `&line=${firstMatchLine}&query=${encodeURIComponent(result.query || '')}`;
      }
      
      fetch(url)
        .then(response => {
          if (response.ok) {
            setIsMatchPage(useFirstMatch);
            return response.blob();
          }
          throw new Error('Failed to load preview');
        })
        .then(blob => {
          // Release previous URL if it exists
          if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
          }
          setPreviewUrl(URL.createObjectURL(blob));
          setIsLoading(false);
        })
        .catch(err => {
          console.error('Error loading preview:', err);
          setIsLoading(false);
          setPreviewError(true);
          setIsMatchPage(false);
          
          // Only try the fallback if we were attempting to load a match page
          if (useFirstMatch) {
            console.log("Falling back to first page preview");
            loadPreview(false);
          }
        });
    } else {
      setIsLoading(false);
    }
  };
  
  // Load preview on mount or when result changes
  useEffect(() => {
    loadPreview();
    
    // Cleanup function to revoke object URL
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [result.qp_path, result.matches]);
  
  // Helper function to highlight matches in text
  const highlightMatches = (text, query) => {
    if (!query || !text) return text;
    
    try {
      const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      const parts = text.split(regex);
      
      return parts.map((part, i) => 
        regex.test(part) ? <span key={`${itemId}-highlight-${i}`} className="highlight bg-yellow-200 font-medium">{part}</span> : part
      );
    } catch (e) {
      // If regex fails (e.g., with special characters), just return the text
      return text;
    }
  };

  // Handle escape key to close modal
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        setShowMatchModal(false);
      }
    };
    
    window.addEventListener('keydown', handleEsc);
    
    return () => {
      window.removeEventListener('keydown', handleEsc);
    };
  }, []);

  // Handler for opening the full paper
  const openFullPaper = () => {
    if (result.qp_path) {
      window.open(`/api/files?path=${encodeURIComponent(result.qp_path)}`, '_blank');
    }
  };
  
  // Navigate through matches
  const nextMatch = () => {
    if (activeMatchIndex < result.matches.length - 1) {
      setActiveMatchIndex(activeMatchIndex + 1);
    } else {
      setActiveMatchIndex(0); // Loop back to first match
    }
  };
  
  const prevMatch = () => {
    if (activeMatchIndex > 0) {
      setActiveMatchIndex(activeMatchIndex - 1);
    } else {
      setActiveMatchIndex(result.matches.length - 1); // Loop to last match
    }
  };

  return (
    <>
      <div 
        id={itemId}
        className="bg-white rounded-xl shadow-lg overflow-hidden flex flex-col h-full transition-all hover:shadow-xl"
      >
        {/* Paper Info Header */}
        <div className="p-4 bg-gradient-to-r from-indigo-600 to-indigo-500 text-white">
          <h3 className="font-semibold text-lg">
            {result.subject} {result.unit ? `Unit ${result.unit}` : ''} 
          </h3>
          <p className="text-indigo-100 text-sm flex justify-between items-center">
            <span>{result.month} {result.year}</span>
            
            {/* Match button in header */}
            {result.matches?.length > 0 && (
              <button 
                className={`ml-auto text-xs font-medium px-3 py-1 rounded-full shadow-sm flex items-center transition-colors ${showMatchPreview ? 'bg-white text-indigo-600' : 'bg-indigo-400 hover:bg-indigo-300 text-white'}`}
                onClick={() => setShowMatchPreview(!showMatchPreview)}
              >
                <Search size={12} className="mr-1" />
                {result.matches.length} {result.matches.length === 1 ? 'match' : 'matches'}
              </button>
            )}
          </p>
        </div>

        {/* Preview Image Container */}
        <div className="relative w-full aspect-[1/1.414] bg-gray-100 flex items-center justify-center overflow-hidden">
          {isLoading ? (
            <div className="flex flex-col items-center text-gray-400">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
              <p className="text-sm mt-3">Loading preview...</p>
            </div>
          ) : previewUrl ? (
            <>
              {/* Actual preview image that opens the full paper when clicked */}
              <div className="w-full h-full cursor-pointer" onClick={openFullPaper}>
                <img 
                  src={previewUrl} 
                  alt={`${result.subject} paper preview`} 
                  className="object-contain w-full h-full p-2"
                />
                
                {/* Central overlay with "View Full Paper" - only appears on hover */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div 
                    className="bg-black/70 text-white font-medium px-4 py-2 rounded-lg shadow-lg flex items-center opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <File size={16} className="mr-2" />
                    View Full Paper
                  </div>
                </div>
              </div>
              
              {/* Page type indicator with improved visibility */}
              <div className="absolute bottom-4 left-4 flex space-x-2 z-10 pointer-events-none">
                {isMatchPage ? (
                  <div className="bg-yellow-400 text-xs font-bold px-3 py-1 rounded-full shadow-md flex items-center">
                    <span className="w-2 h-2 bg-yellow-600 rounded-full mr-1.5 animate-pulse"></span>
                    Match Page
                  </div>
                ) : (
                  <div className="bg-blue-400 text-xs font-bold px-3 py-1 rounded-full shadow-md flex items-center">
                    <span className="w-2 h-2 bg-blue-600 rounded-full mr-1.5"></span>
                    First Page
                  </div>
                )}
              </div>
              
              {/* View Match Text Button - stays visible and clickable */}
              {result.matches?.length > 0 && (
                <div className="absolute top-4 left-4 flex flex-col space-y-2 z-20">
                  <button 
                    className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-3 py-1.5 rounded-lg shadow-md flex items-center transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowMatchPreview(!showMatchPreview);
                    }}
                    title="Toggle match context"
                  >
                    <Eye size={14} className="mr-1.5" />
                    View Match Text
                  </button>
                  
                  {/* Match count badge */}
                  <div className="bg-yellow-500 text-xs font-medium px-2.5 py-1 rounded-lg text-center shadow-sm">
                    {result.matches.length} {result.matches.length === 1 ? 'match' : 'matches'}
                  </div>
                </div>
              )}
              
              {/* Page flip button - larger and more visible */}
              <button 
                className="absolute bottom-4 right-4 bg-gray-800 hover:bg-gray-900 text-white rounded-full p-2.5 shadow-md transition-colors z-20"
                onClick={(e) => {
                  e.stopPropagation();
                  loadPreview(!isMatchPage);
                }}
                title={isMatchPage ? "Show first page" : "Show match page"}
              >
                <RefreshCw size={18} />
              </button>
            </>
          ) : (
            <div className="flex flex-col items-center text-gray-400">
              <File size={40} />
              <p className="text-sm mt-3">Preview not available</p>
            </div>
          )}
        </div>
        
        {/* Elegant Inline Match Preview - with improved visibility */}
        {showMatchPreview && result.matches?.length > 0 && (
          <div className="bg-indigo-50 border-t border-indigo-100 overflow-hidden transition-all">
            <div className="p-4 bg-white border-b border-indigo-100 flex justify-between items-center">
              <div className="flex items-center">
                <div className="bg-indigo-600 text-white text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center shadow-sm mr-3">
                  {activeMatchIndex + 1}
                </div>
                <div>
                  <span className="text-sm font-medium">Match Text {activeMatchIndex + 1} of {result.matches.length}</span>
                  <span className="text-xs text-gray-500 block">Line {result.matches[activeMatchIndex].line}</span>
                </div>
              </div>
              
              <div className="flex space-x-2">
                <button 
                  onClick={prevMatch}
                  className="p-1.5 bg-gray-200 hover:bg-gray-300 rounded-md transition-colors"
                  disabled={result.matches.length <= 1}
                  title="Previous match"
                >
                  <ChevronUp size={16} />
                </button>
                <button 
                  onClick={nextMatch}
                  className="p-1.5 bg-gray-200 hover:bg-gray-300 rounded-md transition-colors"
                  disabled={result.matches.length <= 1}
                  title="Next match"
                >
                  <ChevronDown size={16} />
                </button>
                <button 
                  onClick={() => setShowMatchPreview(false)}
                  className="p-1.5 bg-gray-200 hover:bg-gray-300 rounded-md transition-colors"
                  title="Close match preview"
                >
                  <X size={16} />
                </button>
              </div>
            </div>
            
            <div className="p-4 bg-indigo-50 relative max-h-56 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
              <div className="font-mono text-sm whitespace-pre-wrap bg-white p-3 rounded border border-indigo-100 shadow-sm">
                {highlightMatches(result.matches[activeMatchIndex].original_context, result.query)}
              </div>
              
              {/* View all matches button with improved styling */}
              <button 
                onClick={() => {
                  setShowMatchModal(true);
                  setShowMatchPreview(false);
                }}
                className="mt-3 text-sm bg-indigo-100 text-indigo-700 hover:bg-indigo-200 font-medium flex items-center justify-center w-full py-2 rounded-md transition-colors"
              >
                <Search size={14} className="mr-1.5" />
                View all {result.matches.length} matches
              </button>
            </div>
          </div>
        )}

        {/* Action Buttons - Redesigned */}
        <div className="px-4 py-3 bg-gray-50 flex space-x-2 mt-auto">
          {result.qp_path && (
            <a 
              href={`/api/files?path=${encodeURIComponent(result.qp_path)}`} 
              target="_blank"
              className="flex-1 inline-flex justify-center items-center py-2.5 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              <File size={16} className="mr-1.5" />
              Question Paper
            </a>
          )}
          
          {result.ms_path && (
            <a 
              href={`/api/files?path=${encodeURIComponent(result.ms_path)}`} 
              target="_blank"
              className="flex-1 inline-flex justify-center items-center py-2.5 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700 transition-colors"
            >
              <FileText size={16} className="mr-1.5" />
              Mark Scheme
            </a>
          )}
        </div>
      </div>
      
      {/* Match Modal - Kept for viewing all matches */}
      {showMatchModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 backdrop-blur-sm" onClick={() => setShowMatchModal(false)}>
          <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[85vh] overflow-hidden" onClick={e => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-indigo-700 to-indigo-600 text-white px-6 py-4 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-lg">
                  {result.subject} {result.unit ? `Unit ${result.unit}` : ''} - {result.month} {result.year}
                </h3>
                <p className="text-indigo-100 text-sm">
                  Found {result.matches.length} {result.matches.length === 1 ? 'match' : 'matches'} for "{result.query}"
                </p>
              </div>
              <button 
                className="text-white hover:bg-indigo-800/50 p-2 rounded-full transition-colors"
                onClick={() => setShowMatchModal(false)}
              >
                <X size={20} />
              </button>
            </div>
            
            {/* Match List */}
            <div className="overflow-y-auto p-6 max-h-[calc(85vh-130px)]">
              <div className="space-y-4">
                {result.matches.map((match, index) => (
                  <div 
                    key={`${itemId}-modal-match-${index}`} 
                    className={`bg-gray-50 p-4 rounded-lg border ${index === activeMatchIndex ? 'border-indigo-400 ring-2 ring-indigo-100' : 'border-gray-200'} relative hover:border-indigo-300 transition-colors`}
                  >
                    <div className="absolute -left-2 top-4 bg-indigo-600 text-white text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center shadow-md">
                      {index + 1}
                    </div>
                    <div className="mb-2 text-sm font-medium text-gray-600 pl-6">
                      Line {match.line}
                    </div>
                    <div className="whitespace-pre-wrap font-mono text-sm bg-white p-4 rounded border border-gray-100 shadow-sm">
                      {highlightMatches(match.original_context, result.query)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Modal Footer */}
            <div className="border-t border-gray-200 px-6 py-3 bg-gray-50 flex justify-between">
              <a 
                href={`/api/files?path=${encodeURIComponent(result.qp_path)}`} 
                target="_blank"
                className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition-colors flex items-center"
              >
                <File size={16} className="mr-1.5" />
                Open Full Paper
              </a>
              <button 
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md text-sm hover:bg-gray-300 transition-colors"
                onClick={() => setShowMatchModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default ResultItem;