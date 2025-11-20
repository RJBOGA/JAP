// src/frontend-react/src/CompleteProfilePage.js
import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from './api';
import './App.css'; // Reuse styles

const CompleteProfilePage = () => {
  const { userId } = useParams(); // Get the UserID from the URL
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      setErrorMessage('Please select a resume file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('resume', file);
    
    setStatus('uploading');
    setErrorMessage('');

    try {
      await apiClient.post(`/users/${userId}/resume`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setStatus('success');
      alert('Success! Your profile is being updated with your resume details.');
      navigate('/login'); // Redirect to login after success
    } catch (error) {
      setStatus('error');
      const msg = error.response?.data?.error || 'Upload failed. Please try again.';
      setErrorMessage(msg);
    }
  };

  return (
    <div className="login-container">
      <div className="resume-uploader-panel" style={{ maxWidth: '500px' }}>
        <h2>Welcome! Your account is created.</h2>
        <p>Optionally, you can upload your resume now to auto-fill your profile details.</p>
        
        <div className="uploader-controls">
          <input type="file" onChange={handleFileChange} accept=".pdf,.docx" disabled={status === 'uploading'} />
          <button onClick={handleUpload} disabled={status === 'uploading'}>
            {status === 'uploading' ? 'Analyzing...' : 'Upload & Auto-Fill'}
          </button>
        </div>
        
        <button onClick={() => navigate('/login')} className="skip-button" style={{ marginTop: '20px' }}>
          Skip for Now
        </button>
        
        {status === 'error' && <p className="status-error" style={{ marginTop: '15px' }}>❌ {errorMessage}</p>}
      </div>
    </div>
  );
};

export default CompleteProfilePage;