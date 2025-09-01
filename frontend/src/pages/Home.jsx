import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router';
import aiService from '../services/aiService';

const Home = () => {
  const { user } = useAuth();
  const [query, setQuery] = useState('');
  const [aiResponse, setAiResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a question.');
      return;
    }
    setLoading(true);
    setError('');
    setAiResponse(null);
    try {
      const response = await aiService.query(query);
      setAiResponse(response);
    } catch (err) {
      setError(err.message || 'An error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const renderTable = (results) => {
    const { columns, rows } = results;
    if (!rows || rows.length === 0) {
      return <p>No data to display.</p>;
    }
    const headers = columns || Object.keys(rows[0]);
    return (
      <table style={{ width: '100%', marginTop: '1rem', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {headers.map(header => <th key={header} style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'center', backgroundColor: '#f2f2f2', color: 'black' }}>{header}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} style={{ border: '1px solid #ddd' }}>
              {headers.map(header => <td key={header} style={{ border: '1px solid #ddd', padding: '8px' }}>{String(row[header])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  return (
    <div>
      <h1>Smart Home Energy Monitor</h1>
      {user ? (
        <>
          <p>Hello, {user.name}!</p>
          <p>
            <Link to="/devices">View your device dashboard</Link>
          </p>

          <div style={{ marginTop: '2rem' }}>
            <h2>Ask a question about your energy usage</h2>
            <form onSubmit={handleQuery}>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Which device used the most energy yesterday?"
                style={{ width: '400px', padding: '8px' }}
              />
              <button type="submit" disabled={loading} style={{ padding: '8px 12px', marginLeft: '1rem' }}>
                {loading ? 'Asking...' : 'Ask'}
              </button>
            </form>

            {error && <p style={{ color: 'red' }}>{error}</p>}
            
            {aiResponse && (
              <div style={{ marginTop: '2rem', padding: '1rem', border: '1px solid #eee', borderRadius: '5px' }}>
                <h3>Answer</h3>
                <p>{aiResponse.answer}</p>
                {aiResponse.results && (
                  <>
                    <h4>Data</h4>
                    {renderTable(aiResponse.results)}
                  </>
                )}
              </div>
            )}
          </div>
        </>
      ) : (
        <p>Please log in or register to continue.</p>
      )}
    </div>
  );
};

export default Home;
