// src/frontend-react/src/LoginPage.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './LoginPage.css';

const API_ENDPOINT = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:8000';

function LoginPage() {
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Applicant');
  const [isLogin, setIsLogin] = useState(true);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (isLogin) {
      // --- Sign-In Logic with Persistent Session ---
      try {
        const payload = { email, password };
        const response = await axios.post(`${API_ENDPOINT}/login`, payload);
        
        const expirationTime = new Date().getTime() + (48 * 60 * 60 * 1000); // 48 hours in milliseconds
        const sessionData = {
          user: response.data.user,
          expiresAt: expirationTime,
        };

        localStorage.setItem('session', JSON.stringify(sessionData));
        navigate('/chat');

      } catch (error) {
        if (error.response && error.response.data.error) {
          alert(`Login failed: ${error.response.data.error}`);
        } else {
          alert('Login failed: An unknown error occurred.');
        }
        console.error('Login error:', error);
      }
    } else {
      // --- UPDATED Registration Logic ---
      try {
        const payload = { email, firstName, lastName, password, role };
        const response = await axios.post(`${API_ENDPOINT}/register`, payload);

        // On success, get the new UserID from the response
        const newUserId = response.data.UserID;
        
        // Redirect to the new profile completion page, passing the ID in the URL
        navigate(`/complete-profile/${newUserId}`);

      } catch (error) {
        if (error.response && error.response.data.error) {
          alert(`Registration failed: ${error.response.data.error}`);
        } else {
          alert('Registration failed: An unknown error occurred.');
        }
        console.error('Registration error:', error);
      }
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit} className="login-form">
        <h2>{isLogin ? 'Sign In to JobChat.AI' : 'Create Your Account'}</h2>
        
        {!isLogin && (
          <>
            <div className="input-group">
              <label>First Name</label>
              <input type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
            </div>
            <div className="input-group">
              <label>Last Name</label>
              <input type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} required />
            </div>
            <div className="input-group">
              <label>I am a</label>
              <select value={role} onChange={(e) => setRole(e.target.value)} required>
                <option value="Applicant">User / Applicant</option>
                <option value="Recruiter">Recruiter</option>
              </select>
            </div>
          </>
        )}

        <div className="input-group">
          <label>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>

        <div className="input-group">
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        
        <button type="submit" className="login-button">
          {isLogin ? 'Sign In' : 'Sign Up'}
        </button>
        
        <p className="toggle-form">
          {isLogin ? "Don't have an account?" : "Already have an account?"}
          <button type="button" onClick={() => setIsLogin(!isLogin)} className="toggle-button">
            {isLogin ? 'Sign Up' : 'Sign In'}
          </button>
        </p>
      </form>
    </div>
  );
}

export default LoginPage;