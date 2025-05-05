import { useState } from 'preact/hooks';
import { Search } from 'preact-feather';

function SearchBar({ setResults, setIsLoading, setError }) {
  const [query, setQuery] = useState('');
  const [subjects, setSubjects] = useState('');
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [contextLines, setContextLines] = useState(2);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // We'll implement this function in the API module later
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          subjects: subjects ? subjects.split(',').map(s => s.trim()) : null,
          caseSensitive,
          contextLines
        }),
      });
      
      if (!response.ok) {
        throw new Error('Search failed. Please try again.');
      }
      
      const data = await response.json();
      setResults(data);
    } catch (error) {
      setError(error.message);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-gray-700 font-medium mb-2" htmlFor="query">
            Search Query
          </label>
          <div className="relative">
            <input
              type="text"
              id="query"
              className="w-full px-4 py-2 pr-10 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Enter search terms..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <div className="absolute right-3 top-2 text-gray-400">
              <Search size={20} />
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-gray-700 font-medium mb-2" htmlFor="subjects">
              Subjects (optional, comma separated)
            </label>
            <input
              type="text"
              id="subjects"
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="mathematics,chemistry"
              value={subjects}
              onChange={(e) => setSubjects(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-gray-700 font-medium mb-2" htmlFor="context">
              Context Lines
            </label>
            <input
              type="number"
              id="context"
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              min="1"
              max="10"
              value={contextLines}
              onChange={(e) => setContextLines(Number(e.target.value))}
            />
          </div>
        </div>
        
        <div className="flex items-center mb-4">
          <input
            type="checkbox"
            id="caseSensitive"
            className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
            checked={caseSensitive}
            onChange={(e) => setCaseSensitive(e.target.checked)}
          />
          <label className="ml-2 text-gray-700" htmlFor="caseSensitive">
            Case Sensitive
          </label>
        </div>
        
        <button
          type="submit"
          className="w-full bg-primary hover:bg-indigo-600 text-white font-medium py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
        >
          Search Papers
        </button>
      </form>
    </div>
  );
}

export default SearchBar;