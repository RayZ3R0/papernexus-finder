import { useState } from 'preact/hooks';
import SearchBar from './SearchBar';
import ResultsList from './ResultsList';

export function App() {
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-primary shadow-md">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-white">PaperNexus Finder</h1>
          <p className="text-blue-100 text-sm">Search through past papers with ease</p>
        </div>
      </header>
      
      <main className="container mx-auto px-4 py-6">
        <SearchBar 
          setResults={setResults} 
          setIsLoading={setIsLoading}
          setError={setError}
        />
        
        {error && (
          <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}
        
        <ResultsList 
          results={results} 
          isLoading={isLoading} 
        />
      </main>
      
      <footer className="bg-gray-800 text-white py-4 mt-8">
        <div className="container mx-auto px-4 text-center text-sm">
          &copy; {new Date().getFullYear()} PaperNexus Finder
        </div>
      </footer>
    </div>
  );
}

export default App;