import ResultItem from './ResultItem';

function ResultsList({ results, isLoading }) {
  if (isLoading) {
    return (
      <div className="mt-8 flex items-center justify-center py-16">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-600 border-t-transparent"></div>
          <p className="mt-4 text-gray-600 font-medium">Searching papers...</p>
        </div>
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <div className="mt-8 bg-white p-10 rounded-xl shadow-md text-center">
        <div className="flex flex-col items-center">
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-16 w-16 text-gray-300 mb-3" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={1.5} 
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" 
            />
          </svg>
          <p className="text-gray-500 text-lg">No search results yet. Try searching for something!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-800">
          Found {results.length} matching papers
        </h2>
        <div className="text-sm text-gray-500">
          Showing papers with matches for your search
        </div>
      </div>
      
      {/* A4 proportional grid (1:1.414 aspect ratio) with larger cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 gap-8">
        {results.map((result, index) => (
          <div key={`result-${index}-${result.subject}-${result.unit || 'nounit'}-${result.year}`} 
               className="flex">
            <ResultItem result={result} />
          </div>
        ))}
      </div>
    </div>
  );
}

export default ResultsList;