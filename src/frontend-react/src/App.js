// src/frontend-react/src/App.js
import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import LoginPage from './LoginPage';
import ResultsDisplay from './ResultsDisplay'; // Import our new component

const NL2GQL_ENDPOINT = process.env.REACT_APP_NL2GQL_ENDPOINT || 'http://localhost:8000/nl2gql';

function ChatPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  // --- This effect runs on component mount to check for a logged-in user ---
  useEffect(() => {
    const storedUser = sessionStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    } else {
      navigate('/login');
    }
  }, [navigate]);

  const handleLogout = () => {
    sessionStorage.removeItem('user');
    setUser(null);
    navigate('/login');
  };

  // --- State and handlers for chat functionality ---
  const [messages, setMessages] = useState([
    // Each message is an object with a 'type', 'role', and 'payload'
    { type: 'text', role: 'assistant', payload: { text: "Hi! Ask me anything about users or jobs." } }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');

  // Effect to apply the theme to the document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(prevTheme => (prevTheme === 'light' ? 'dark' : 'light'));

  const formatContentForDisplay = (content) => {
    // Basic formatting for bold text in simple messages
    return content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userPrompt = input.trim();
    // Add the user's text message to the chat
    setMessages(prev => [...prev, { type: 'text', role: 'user', payload: { text: userPrompt } }]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(NL2GQL_ENDPOINT, { query: userPrompt });
      const { graphql = "", result = {} } = response.data;

      if (graphql === "Small talk handled by service logic" && result.response) {
        // Handle conversational small talk as a simple text message
        setMessages(prev => [...prev, { type: 'text', role: 'assistant', payload: { text: result.response } }]);
      } else {
        // Add a 'results' type message to render with the special component
        setMessages(prev => [...prev, { type: 'results', role: 'assistant', payload: { rawGql: graphql, rawJson: result } }]);
      }
    } catch (error) {
      const err_msg = error.response?.data?.error?.message || "An unexpected error occurred while connecting to the service.";
      // Errors are displayed as simple text messages
      setMessages(prev => [...prev, { type: 'text', role: 'assistant', payload: { text: `**Error:** ${err_msg}` } }]);
    } finally {
      setLoading(false);
    }
  };

  // Render nothing while the authentication check is happening
  if (!user) {
    return null;
  }

  // --- JSX for the ChatPage component ---
  return (
    <div className="App">
      <div className="header-container">
        <h1>JobChat.AI</h1>
        <div className="header-controls">
          <span className="user-greeting">Hi, {user.firstName}!</span>
          <button onClick={toggleTheme} className="theme-toggle">
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
          <button onClick={handleLogout} className="logout-button" title="Logout">
            Logout
          </button>
        </div>
      </div>

      <div className="message-container">
        {messages.map((m, index) => (
          <div key={index} className={`message ${m.role}-message`}>
            {/* Conditionally render the ResultsDisplay or a plain text bubble */}
            {m.type === 'results' ? (
              <ResultsDisplay rawGql={m.payload.rawGql} rawJson={m.payload.rawJson} />
            ) : (
              <div
                className="message-bubble"
                dangerouslySetInnerHTML={{ __html: formatContentForDisplay(m.payload.text) }}
              />
            )}
          </div>
        ))}
      </div>
      
      <form onSubmit={handleSend} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a request like 'find jobs in London'..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? '...' : 'Send'}
        </button>
      </form>
    </div>
  );
}


// --- Main App Component for Routing ---
function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/chat" element={<ChatPage />} />
      
      {/* Set the default route to redirect to the chat page */}
      <Route path="/" element={<Navigate to="/chat" />} />
    </Routes>
  );
}

export default App;