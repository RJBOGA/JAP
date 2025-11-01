import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css'; // Import the new CSS file

const NL2GQL_ENDPOINT = process.env.REACT_APP_NL2GQL_ENDPOINT || 'http://localhost:8000/nl2gql';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hi! Ask me to create, list, update, or delete users in plain English." }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Theme state and persistence
  const [theme, setTheme] = useState(
    () => localStorage.getItem('theme') || 'light'
  );

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === 'light' ? 'dark' : 'light'));
  };

  const formatContentForDisplay = (content) => {
    // Basic Markdown to HTML conversion for strong tags and line breaks
    let html = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Escape backticks for code blocks, but keep the structure
    html = html.replace(/```(.*?)\n([\s\S]*?)```/g, (match, p1, p2) => {
        const codeType = p1.trim() || 'text';
        const escapedCode = p2.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return `<pre><code>${escapedCode}</code></pre>`;
    });
    // Convert remaining newlines to <br/> outside of code blocks (handled by pre-wrap in CSS)
    // The previous implementation used dangerouslySetInnerHTML and line breaks, which is okay for this context.
    // We rely on CSS 'white-space: pre-wrap' for readability and keep the strong tags/code block logic.
    return html;
  };


  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userPrompt = input.trim();
    const newUserMessage = { role: 'user', content: userPrompt };
    
    // 1. Add user message to chat
    setMessages((prevMessages) => [...prevMessages, newUserMessage]);
    setInput('');
    setLoading(true);

    let assistantText = '';
    
    try {
      // 2. Call backend NL2GQL
      const response = await axios.post(NL2GQL_ENDPOINT, { query: userPrompt });

      // 3. Handle 200 Success
      const data = response.data;
      const gql = data.graphql || "";
      const result = data.result || {};
      
      assistantText = 
        `**Generated GraphQL:**\n\n\`\`\`graphql\n${gql}\n\`\`\`\n\n` +
        `**Result:**\n\n\`\`\`json\n${JSON.stringify(result, null, 2)}\n\`\`\``;

    } catch (error) {
      // 4. Handle Errors
      let err_msg = "An unexpected error occurred.";
      const examples = [
        "find user named Raju",
        "find user born on 2000-05-01",
        "update user Raju’s last name to Booo",
        "delete user named Raju born on 2000-05-01",
      ];
      
      if (error.response) {
        // Backend returned a non-2xx status (e.g., 400 or 500)
        const err = error.response.data?.error;
        if (err && err.message) {
            err_msg = err.message;
        } else {
            err_msg = `NL→GQL service returned status ${error.response.status}. Unable to parse error message.`;
        }
      } else if (error.request) {
        // Request was made but no response received (e.g., connection error)
        err_msg = "Error: Could not connect to the NL→GQL service. Is the backend running?";
      } else {
        // General error (e.g., timeout, setup issue)
        err_msg = `An unexpected error occurred: ${error.message}`;
      }
      
      assistantText = `**Error:** ${err_msg}\n\n**Examples:**\n\n` + examples.map(e => `"${e}"`).join("\n\n");

    } finally {
      setLoading(false);
      // 5. Add assistant message to chat
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

export default App;