// src/frontend-react/src/ResumeUploader.js
import React, { useState } from 'react';
import apiClient from './api';
import './App.css'; // Reuse some styles

const ResumeUploader = ({ target, onComplete }) => {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | uploading | success | error
  const [errorMessage, setErrorMessage] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      setErrorMessage('Please select a file first.');
      return;
    }
    
    const formData = new FormData();
    formData.append('resume', file);
    
    setStatus('uploading');
    setErrorMessage('');

    try {
      await apiClient.post(`/applications/${target.appId}/resume`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setStatus('success');
      // Automatically close the uploader after 2 seconds
      setTimeout(() => onComplete(), 2000);
    } catch (error) {
      setStatus('error');
      const msg = error.response?.data?.error || 'Upload failed. Please try again.';
      setErrorMessage(msg);
    }
  };

  return (
    <div className="resume-uploader-panel">
      <h4>Application for "{target.jobTitle}" successful!</h4>
      <p>Next, please upload your resume (PDF or DOCX).</p>
      
      {status !== 'success' && (
        <div className="uploader-controls">
          <input type="file" onChange={handleFileChange} accept=".pdf,.docx" disabled={status === 'uploading'} />
          <button onClick={handleUpload} disabled={status === 'uploading'}>
            {status === 'uploading' ? 'Uploading...' : 'Upload Resume'}
          </button>
          <button onClick={onComplete} className="skip-button" disabled={status === 'uploading'}>Skip for now</button>
        </div>
      )}
      
      {status === 'success' && <p className="status-success">✅ Resume uploaded successfully!</p>}
      {status === 'error' && <p className="status-error">❌ {errorMessage}</p>}
    </div>
  );
};

export default ResumeUploader;