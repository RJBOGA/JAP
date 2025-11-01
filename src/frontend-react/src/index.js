import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './App.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Note: A real setup would also need an HTML file (index.html) 
// and potentially CSS, but 'react-scripts start' handles index.html creation.
