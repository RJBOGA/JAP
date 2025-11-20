// src/frontend-react/src/App.js
import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import './App.css';
import LoginPage from './LoginPage';
import ResultsDisplay from './ResultsDisplay';
import apiClient from './api';
import ResumeUploader from './ResumeUploader'; // Import the new uploader component
import CompleteProfilePage from './CompleteProfilePage';

function ChatPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [uploadTarget, setUploadTarget] = useState(null); // State to trigger the uploader UI

  // --- This effect checks for a valid, non-expired session on component load ---
  useEffect(() => {
    const sessionJSON = localStorage.getItem('session');
    
    if (sessionJSON) {
      const session = JSON.parse(sessionJSON);
      const now = new Date().getTime();

      if (now > session.expiresAt) {
        localStorage.removeItem('session');
        navigate('/login');
      } else {
        setUser(session.user);
      }
    } else {
      navigate('/login');
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('session');
    setUser(null);
    navigate('/login');
  };

  // --- State and handlers for chat functionality ---
  const [messages, setMessages] = useState([
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
    return content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userPrompt = input.trim();
    setMessages(prev => [...prev, { type: 'text', role: 'user', payload: { text: userPrompt } }]);
    setInput('');
    setLoading(true);

    try {
      const payload = { 
        query: userPrompt,
        userContext: user
      };
      
      const response = await apiClient.post('/nl2gql', payload);
      const { graphql = "", result = {} } = response.data;

      // Check for a successful 'apply' mutation to trigger the resume uploader
      if (result.data?.apply) {
        const application = result.data.apply;
        setUploadTarget({
          appId: application.appId,
          jobTitle: application.job.title,
        });
        // Add the success message to the chat first
        setMessages(prev => [...prev, { type: 'results', role: 'assistant', payload: { rawGql: graphql, rawJson: result } }]);
      }
      else if (graphql === "Small talk handled by service logic" && result.response) {
        setMessages(prev => [...prev, { type: 'text', role: 'assistant', payload: { text: result.response } }]);
      } else {
        setMessages(prev => [...prev, { type: 'results', role: 'assistant', payload: { rawGql: graphql, rawJson: result } }]);
      }
    } catch (error) {
      const err_msg = error.response?.data?.error?.message || "An unexpected error occurred while connecting to the service.";
      setMessages(prev => [...prev, { type: 'text', role: 'assistant', payload: { text: `**Error:** ${err_msg}` } }]);
    } finally {
      setLoading(false);
    }
  };

  // Render nothing until the authentication check is complete
  if (!user) {
    return null;
  }

  // --- JSX for the ChatPage component ---
  return (
    <div className="App">
      <div className="header-container">
        <h1>JobChat.AI</h1>
        <div className="header-controls">
          <span className="user-greeting">Hi, {user.firstName}! ({user.role})</span>
          <button onClick={toggleTheme} className="theme-toggle">
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
          <button onClick={handleLogout} className="logout-button" title="Logout">
            Logout
          </button>
        </div>
      </div>

      {user.role === 'Recruiter' && (
        <div className="recruiter-panel">
          <p>Recruiter Tools: You can now post jobs. Try asking: "create a job for a Senior Python Developer at Google..."</p>
        </div>
      )}

      <div className="message-container">
        {messages.map((m, index) => (
          <div key={index} className={`message ${m.role}-message`}>
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
      
      {/* Conditionally render the ResumeUploader when a target is set */}
      {uploadTarget && (
        <ResumeUploader 
          target={uploadTarget} 
          onComplete={() => setUploadTarget(null)} 
        />
      )}
      
      <form onSubmit={handleSend} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a request like 'find jobs in London'..."
          disabled={loading || !!uploadTarget} // Disable input while uploader is active
        />
        <button type="submit" disabled={loading || !!uploadTarget}>
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
      <Route path="/complete-profile/:userId" element={<CompleteProfilePage />} />
      <Route path="/" element={<Navigate to="/chat" />} />
    </Routes>
  );
}

export default App;