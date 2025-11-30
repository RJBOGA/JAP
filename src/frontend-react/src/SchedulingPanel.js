import React, { useState, useEffect } from 'react';
import apiClient from './api';
import './App.css'; // Reuses styles

const SchedulingPanel = ({ target, onClose, recruiterId }) => {
  const [slots, setSlots] = useState(null);
  const [status, setStatus] = useState('loading'); // loading | loaded | error | confirmed | confirming
  const [error, setError] = useState('');

  // --- Step 1: Fetch Available Slots on Load ---
  useEffect(() => {
    const fetchSlots = async () => {
      try {
        // Query the new resolver: findAvailableSlots
        const response = await apiClient.post('/graphql', {
          query: `
            query FindSlots($candidateId: Int!) {
              findAvailableSlots(candidateId: $candidateId, durationMinutes: 30, numDays: 7)
            }
          `,
          variables: { candidateId: target.candidateId },
        });

        const availableSlots = response.data.data.findAvailableSlots;
        setSlots(availableSlots || []);
        setStatus('loaded');
      } catch (err) {
        console.error("Error fetching slots:", err);
        setError("Failed to fetch slots. Is your Recruiter availability set?");
        setStatus('error');
      }
    };
    fetchSlots();
  }, [target.candidateId]);

  // --- Step 2: Book the Chosen Slot ---
  const handleBookSlot = async (startTimeISO) => {
    setStatus('confirming');
    setError('');
    const endTime = new Date(new Date(startTimeISO).getTime() + 30 * 60000).toISOString(); // Calculate +30 min

    try {
      const response = await apiClient.post('/graphql', {
        query: `
          mutation BookInterview($jobId: Int!, $candidateId: Int!, $startTime: String!, $endTime: String!) {
            bookInterview(
              jobId: $jobId,
              candidateId: $candidateId,
              startTime: $startTime,
              endTime: $endTime
            ) {
              interviewId
              startTime
              candidate { firstName }
            }
          }
        `,
        variables: {
          jobId: target.jobId,
          candidateId: target.candidateId,
          startTime: startTimeISO,
          endTime: endTime,
        },
      });

      if (response.data.errors) {
        throw new Error(response.data.errors[0].message);
      }

      setStatus('confirmed');
      // The email and status update are handled by the backend book_interview service now!

    } catch (err) {
      console.error("Booking Error:", err);
      setError(err.message && typeof err.message === 'string' && err.message.includes("Conflict detected") ? "Conflict: That slot was just booked or is unavailable!" : (err.message || 'Booking failed'));
      setStatus('loaded'); // Return to selection screen on soft error
    }
  };
  
  // Helper to format ISO string to readable time
  const formatTime = (isoString) => {
    return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // Helper to format ISO string to readable date
  const formatDate = (isoString) => {
      return new Date(isoString).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
  }

  // --- Render Logic ---
  return (
    <div className="scheduling-panel">
      <h3>Schedule Interview with {target.candidateName}</h3>
      <p>Role: {target.jobTitle}</p>

      {status === 'loading' && <p>Searching for conflict-free slots...</p>}
      
      {status === 'error' && <p className="status-error">❌ {error}</p>}

      {status === 'confirming' && <p>Booking selected slot...</p>}

      {status === 'confirmed' && (
        <div className="status-success">
          ✅ Interview successfully booked and invitation sent!
        </div>
      )}

      {status === 'loaded' && (
        <>
          <p>Select an available 30-minute slot:</p>
          <div className="slot-list">
            {slots && slots.length > 0 ? (
              slots.map((slot, index) => (
                <button
                  key={index}
                  className="slot-button"
                  onClick={() => handleBookSlot(slot)}
                >
                  {formatDate(slot)} at {formatTime(slot)}
                </button>
              ))
            ) : (
              <p>No open slots found for the next 7 days. Please check Recruiter availability.</p>
            )}
          </div>
          {error && <p className="status-error" style={{marginTop: '10px'}}>❌ {error}</p>}
        </>
      )}
      
      <button onClick={onClose} className="skip-button" style={{ marginTop: '20px' }} disabled={status === 'confirming'}>
        {status === 'confirmed' ? 'Done' : 'Cancel'}
      </button>
    </div>
  );
};

export default SchedulingPanel;
