// src/frontend-react/src/App.js
import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import LoginPage from './LoginPage';

const NL2GQL_ENDPOINT = process.env.REACT_APP_NL2GQL_ENDPOINT || 'http://localhost:8000/nl2gql';

function ChatPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null); // State to hold user data

  // --- This effect runs when the component loads to check for a logged-in user ---
  useEffect(() => {
    const storedUser = sessionStorage.getItem('user');
    if (storedUser) {
      // If user data exists in session, parse and set it to state
      setUser(JSON.parse(storedUser));
    } else {
      // If no user is found in session, redirect to the login page
      navigate('/login');
    }
  }, [navigate]);

  const handleLogout = () => {
    // Clear user from session storage
    sessionStorage.removeItem('user');
    // Clear user from component state
    setUser(null);
    // Redirect to the login page
    navigate('/login');
  };

  // --- State and handlers for the chat functionality ---
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hi! Ask me anything about users or jobs." }
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
    let html = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/```(.*?)\n([\s\S]*?)```/g, (match, p1, p2) => {
        const escapedCode = p2.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return `<pre><code>${escapedCode}</code></pre>`;
    });
    return html;
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userPrompt = input.trim();
    setMessages(prevMessages => [...prevMessages, { role: 'user', content: userPrompt }]);
    setInput('');
    setLoading(true);

    let assistantText = '';
    try {
      const response = await axios.post(NL2GQL_ENDPOINT, { query: userPrompt });
      const { graphql = "", result = {} } = response.data;

      if (graphql === "Small talk handled by service logic" && result.response) {
          assistantText = result.response;
      } else {
        assistantText = `**Generated GraphQL:**\n\n\`\`\`graphql\n${graphql}\n\`\`\`\n\n**Result:**\n\n\`\`\`json\n${JSON.stringify(result, null, 2)}\n\`\`\``;
      }
    } catch (error) {
      const err_msg = error.response?.data?.error?.message || "An unexpected error occurred while connecting to the service.";
      assistantText = `**Error:** ${err_msg}`;
    } finally {
      setLoading(false);
      setMessages(prevMessages => [...prevMessages, { role: 'assistant', content: assistantText }]);
    }
  };

  // Render nothing (or a loading spinner) until the user check is complete
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
            <div 
              className="message-bubble" 
              dangerouslySetInnerHTML={{ __html: formatContentForDisplay(m.content) }}
            />
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