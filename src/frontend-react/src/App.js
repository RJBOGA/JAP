// src/frontend-react/src/App.js
import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom'; // Import routing components
import axios from 'axios';
import './App.css';

const NL2GQL_ENDPOINT = process.env.REACT_APP_NL2GQL_ENDPOINT || 'http://localhost:8000/nl2gql';

// 1. The original App component is now our ChatPage component
function ChatPage() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hi! Ask me to create, list, update, or delete users in plain English." }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === 'light' ? 'dark' : 'light'));
  };

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
    setMessages((prevMessages) => [...prevMessages, { role: 'user', content: userPrompt }]);
    setInput('');
    setLoading(true);

    let assistantText = '';
    
    try {
      const response = await axios.post(NL2GQL_ENDPOINT, { query: userPrompt });
      const data = response.data;
      const gql = data.graphql || "";
      const result = data.result || {};
      
      if (gql === "Small talk handled by service logic" && result.response) {
          assistantText = result.response;
      } else {
        assistantText = 
          `**Generated GraphQL:**\n\n\`\`\`graphql\n${gql}\n\`\`\`\n\n` +
          `**Result:**\n\n\`\`\`json\n${JSON.stringify(result, null, 2)}\n\`\`\``;
      }
    } catch (error) {
      let err_msg = "An unexpected error occurred.";
      if (error.response) {
        const err = error.response.data?.error;
        err_msg = err?.message || `NL→GQL service returned status ${error.response.status}.`;
      } else if (error.request) {
        err_msg = "Error: Could not connect to the NL→GQL service. Is the backend running?";
      } else {
        err_msg = `An unexpected error occurred: ${error.message}`;
      }
      assistantText = `**Error:** ${err_msg}`;
    } finally {
      setLoading(false);
      setMessages((prevMessages) => [...prevMessages, { role: 'assistant', content: assistantText }]);
    }
  };

  return (
    <div className="App">
      <div className="header-container">
        <h1>Job Seeker Chat (React)</h1>
        <button onClick={toggleTheme} className="theme-toggle">
          {theme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
        </button>
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
          placeholder="Type a request like 'create a user named Raj etc.,'."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}


// 2. This is the new main App component that will handle all routing logic
function App() {
  return (
    <Routes>
      {/* This route makes the ChatPage component render at /chat */}
      <Route path="/chat" element={<ChatPage />} />

      {/* This will redirect the user from the base URL (/) to /chat */}
      <Route path="/" element={<Navigate to="/chat" />} />
    </Routes>
  );
}

export default App;