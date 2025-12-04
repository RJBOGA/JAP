import React, { useState, useEffect } from 'react';
import apiClient from './api';
import './App.css'; // Reuses styles

const SchedulingPanel = ({ target, onClose, recruiterId }) => {
  const [slots, setSlots] = useState(null);
  const [status, setStatus] = useState('loading'); // loading | loaded | error | confirmed | confirming
  const [error, setError] = useState('');

  // Determine Mode: Recruiter vs Applicant
  // Recruiter mode passes {candidateId, jobId}. Applicant mode passes {candidateId, jobId, appId}.
  const isApplicantMode = !!target?.appId;

  // --- Step 1: Fetch Available Slots on Load ---
  useEffect(() => {
    const fetchSlots = async () => {
      try {
        const response = await apiClient.post('/graphql', {
          query: `
            query FindSlots($candidateId: Int!, $jobId: Int!) {
              findAvailableSlots(candidateId: $candidateId, jobId: $jobId, durationMinutes: 30, numDays: 7)
            }
          `,
          variables: {
            candidateId: target.candidateId,
            jobId: target.jobId,
          },
        });

        const availableSlots = response.data?.data?.findAvailableSlots;
        setSlots(availableSlots || []);
        setStatus('loaded');
      } catch (err) {
        console.error('Error fetching slots:', err);
        setError('Failed to fetch slots. Availability might not be set.');
        setStatus('error');
      }
    };

    if (target && target.candidateId && target.jobId) fetchSlots();
    else setStatus('error');
  }, [target?.candidateId, target?.jobId]);

  // --- Step 2: Book the Chosen Slot ---
  const handleBookSlot = async (startTimeISO) => {
    setStatus('confirming');
    setError('');
    const endTime = new Date(new Date(startTimeISO).getTime() + 30 * 60000).toISOString(); // Calculate +30 min

    try {
      let query = '';
      let variables = {};

      if (isApplicantMode) {
        // APPLICANT MUTATION
        query = `
          mutation SelectSlot($appId: Int!, $startTime: String!) {
            selectInterviewSlot(appId: $appId, startTime: $startTime) {
              interviewId
              startTime
            }
          }
        `;
        variables = { appId: target.appId, startTime: startTimeISO };
      } else {
        // RECRUITER MUTATION
        query = `
          mutation BookInterview($jobId: Int!, $candidateId: Int!, $startTime: String!, $endTime: String!) {
            bookInterview(
              jobId: $jobId,
              candidateId: $candidateId,
              startTime: $startTime,
              endTime: $endTime
            ) {
              interviewId
              startTime
            }
          }
        `;
        variables = {
          jobId: target.jobId,
          candidateId: target.candidateId,
          startTime: startTimeISO,
          endTime: endTime,
        };
      }

      const response = await apiClient.post('/graphql', { query, variables });

      if (response.data?.errors) {
        throw new Error(response.data.errors[0].message);
      }

      setStatus('confirmed');
    } catch (err) {
      console.error('Booking Error:', err);
      // Friendly conflict message if backend indicates conflict
      const msg = err?.message || '';
      if (msg.includes('Conflict detected')) setError('Conflict: That slot was just booked or is unavailable!');
      else setError(msg || 'Booking failed');
      setStatus('loaded');
    }
  };

  const formatTime = (isoString) => {
    try {
      return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoString;
    }
  };

  const formatDate = (isoString) => {
    try {
      return new Date(isoString).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="scheduling-panel">
      <h3>{isApplicantMode ? 'Select Your Interview Time' : `Schedule Interview with ${target.candidateName}`}</h3>
      <p>Role: {target.jobTitle}</p>

      {status === 'loading' && <p>Searching for available slots...</p>}

      {status === 'error' && <p className="status-error">❌ {error}</p>}

      {status === 'confirming' && <p>Confirming your slot...</p>}

      {status === 'confirmed' && (
        <div className="status-success">✅ Interview confirmed! Check your email for details.</div>
      )}

      {status === 'loaded' && (
        <>
          <p>Available 30-minute slots:</p>
          <div className="slot-list">
            {slots && slots.length > 0 ? (
              slots.map((slot, index) => (
                <button key={index} className="slot-button" onClick={() => handleBookSlot(slot)}>
                  {formatDate(slot)} at {formatTime(slot)}
                </button>
              ))
            ) : (
              <p>No open slots found. Please contact the recruiter.</p>
            )}
          </div>
          {error && <p className="status-error" style={{ marginTop: '10px' }}>❌ {error}</p>}
        </>
      )}

      <button onClick={onClose} className="skip-button" style={{ marginTop: '20px' }} disabled={status === 'confirming'}>
        {status === 'confirmed' ? 'Close' : 'Cancel'}
      </button>
    </div>
  );
};

export default SchedulingPanel;
