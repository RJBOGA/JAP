// src/frontend-react/src/ResultsDisplay.js
import React, { useState } from 'react';
import apiClient from './api'; // <--- IMPORT THIS
import './ResultsDisplay.css';

// A small helper component to render a single Job
const JobResult = ({ job }) => (
  <div className="result-item">
    <div className="item-header">
      <span className="item-title">{job.title || 'N/A'}</span>
      <span className="item-location">{job.location || 'N/A'}</span>
    </div>
    <div className="item-company">{job.company || 'N/A'}</div>
    {job.skillsRequired && job.skillsRequired.length > 0 && (
      <div className="item-skills">
        {job.skillsRequired.map(skill => <span key={skill} className="skill-tag">{skill}</span>)}
      </div>
    )}
  </div>
);

// An enhanced component to render a single, detailed User profile
const UserResult = ({ user, onInviteClick, currentUserRole }) => {
    // Local state to update UI immediately after clicking Hire/Reject
    const [localStatus, setLocalStatus] = useState(user.applicationStatus);
    const [loading, setLoading] = useState(false);

    // Normalize status
    const status = localStatus ? localStatus.toLowerCase() : '';
    const isScheduled = status.includes('interview');
    const isHired = status === 'hired';
    const isRejected = status === 'rejected';

    // Time Check Logic
    let isInterviewPassed = false;
    let buttonText = 'Schedule Interview';

    if (isScheduled) {
        if (user.interviewTime) {
            const interviewDate = new Date(user.interviewTime);
            const now = new Date();
            if (now > interviewDate) {
                isInterviewPassed = true;
            }
            const dateStr = interviewDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const timeStr = interviewDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
            buttonText = `✅ Interview: ${dateStr} at ${timeStr}`;
        } else {
            buttonText = '✅ Interview Scheduled';
        }
    }
    if (isHired) buttonText = '🎉 Hired';
    if (isRejected) buttonText = '❌ Rejected';

    // --- NEW: Handle Hire/Reject Clicks ---
    const handleDecision = async (newStatus) => {
        if (!window.confirm(`Are you sure you want to mark this candidate as ${newStatus}? This will send an email.`)) return;
        
        setLoading(true);
        try {
            await apiClient.post('/graphql', {
                query: `
                  mutation UpdateStatus($userName: String!, $jobTitle: String!, $newStatus: String!) {
                    updateApplicationStatusByNames(
                      userName: $userName,
                      jobTitle: $jobTitle,
                      newStatus: $newStatus
                    ) {
                      status
                    }
                  }
                `,
                variables: {
                    userName: `${user.firstName} ${user.lastName}`,
                    jobTitle: user.jobTitle,
                    newStatus: newStatus
                }
            });
            setLocalStatus(newStatus);
        } catch (err) {
            alert("Failed to update status. Check console.");
            console.error(err);
        } finally {
            setLoading(false);
        }
    };
    // --------------------------------------

    // --- NEW: Security Check ---
    const isRecruiter = currentUserRole === 'Recruiter';

    return (
        <div className="result-item">
            {/* Header / Info Sections (Same as before) */}
            <div className="item-header">
                <span className="item-title">{user.firstName} {user.lastName}</span>
                {localStatus && <StatusBadge status={localStatus} />} 
                {user.is_us_citizen && <span className="citizen-badge">✅ US Citizen</span>}
                <span className="item-location">{user.city && user.country ? `${user.city}, ${user.country}` : ''}</span>
            </div>
            
            <div className="item-subtitle">{user.professionalTitle || '------------'}</div>

            {/* Skills & Details (Same as before) */}
            {user.years_of_experience != null && <div><strong>Experience:</strong> {user.years_of_experience} years</div>}
            {user.highest_qualification && <div><strong>Qualification:</strong> {user.highest_qualification}</div>}
            
            {user.skills && user.skills.length > 0 && (
                <div className="item-skills">
                    {user.skills.map(skill => <span key={skill} className="skill-tag">{skill}</span>)}
                </div>
            )}

            
                        <div className="item-links">
                            {user.linkedin_profile && <a href={user.linkedin_profile} target="_blank" rel="noopener noreferrer">LinkedIn</a>}
                            {user.portfolio_url && <a href={user.portfolio_url} target="_blank" rel="noopener noreferrer">Portfolio</a>}
                            {user.resume_url ? (
                                <a href={`http://localhost:8000${user.resume_url}`} target="_blank" rel="noopener noreferrer" className="resume-link">📄 View Resume</a>
                            ) : (
                                <span className="no-resume">No Resume</span>
                            )}
                        </div>

                        {/* --- ACTION AREA: ONLY SHOW FOR RECRUITERS --- */}
            {isRecruiter && (
                <div className="action-area">
                    {isScheduled && isInterviewPassed && !loading ? (
                        <div className="decision-buttons">
                            <button className="decision-btn hire-btn" onClick={() => handleDecision("Hired")}>
                                🎉 Hire
                            </button>
                            <button className="decision-btn reject-btn" onClick={() => handleDecision("Rejected")}>
                                ❌ Reject
                            </button>
                        </div>
                    ) : (
                        onInviteClick && user.jobId && user.UserID && (
                            <button 
                                className={`action-button ${isScheduled || isRejected || isHired ? 'disabled-button' : 'invite-button'}`}
                                disabled={isScheduled || isRejected || isHired || loading}
                                onClick={() => onInviteClick(user.UserID, user.jobId, `${user.firstName} ${user.lastName}`, user.jobTitle)}
                            >
                                {loading ? 'Updating...' : buttonText}
                            </button>
                        )
                    )}
                </div>
            )}
        </div>
    );
};

// A helper component to render an application card (for user's own applications)
const ApplicationResult = ({ app }) => (
    <div className="result-item">
        <div className="item-header">
            <span className="item-title">{app.job?.title || 'N/A'}</span>
            <span className="item-status">{app.status}</span>
        </div>
        <div className="item-company">{app.job?.company || 'N/A'}</div>
        {app.notes && (
            <div className="item-notes">
                <strong>Your Notes:</strong> {app.notes}
            </div>
        )}
    </div>
);


const ResultsDisplay = ({ rawGql, rawJson, onInviteClick, currentUserRole }) => {
  const [detailsVisible, setDetailsVisible] = useState(false);

  let resultsContent = null;
  const resultData = rawJson?.data;

  // Check for different types of data and prepare the display content
  if (resultData) {
      // Handles a list of the user's own applications
      if (resultData.applications && Array.isArray(resultData.applications)) {
          resultsContent = (
              <div className="result-item job-applicant-container">
                  <h3 className="container-title">Your Applications</h3>
                  {resultData.applications.length > 0 ? (
                      resultData.applications.map(app => <ApplicationResult key={app.appId} app={app} />)
                  ) : (
                      <p>You have not applied to any jobs yet.</p>
                  )}
              </div>
          );
      }
      // Handles the result of updating an application status or adding a note
      else if (resultData.updateApplicationStatusByNames || resultData.addNoteToApplicationByJob) {
          const app = resultData.updateApplicationStatusByNames || resultData.addNoteToApplicationByJob;
          resultsContent = <ApplicationResult app={app} />;
      }
      // Handles a request for jobs that includes an application count
      else if (resultData.jobs && Array.isArray(resultData.jobs) && resultData.jobs[0]?.applicationCount !== undefined) {
          resultsContent = resultData.jobs.map(job => (
              <div key={job.jobId} className="result-item application-count-result">
                  The job "{job.title}" at {job.company} has {job.applicationCount} application's.
              </div>
          ));
      }
      // Handles a request for jobs with nested applicants
      else if (resultData.jobs && Array.isArray(resultData.jobs) && resultData.jobs[0]?.applicants) {
          resultsContent = resultData.jobs.map(job => (
              <div key={job.jobId} className="result-item job-applicant-container">
                  <h3 className="container-title">Applicants for: {job.title} at {job.company}</h3>
                      {job.applicants.length > 0 ? (
                      job.applicants.map(applicant => <UserResult key={applicant.UserID} user={{...applicant, jobId: job.jobId, jobTitle: job.title}} onInviteClick={onInviteClick} />)
                  ) : (
                      <p>No applicants found for this job yet.</p>
                  )}
              </div>
          ));
      }
      // Handles a simple list of jobs
      else if (resultData.jobs && Array.isArray(resultData.jobs)) {
          resultsContent = resultData.jobs.length > 0
            ? resultData.jobs.map(job => <JobResult key={job.jobId} job={job} />)
            : <p>No jobs found matching your criteria.</p>;
      
      // Handles a list of users
            } else if (resultData.users && Array.isArray(resultData.users)) {
                    resultsContent = resultData.users.length > 0
                        ? resultData.users.map(user => <UserResult key={user.UserID} user={user} onInviteClick={onInviteClick} />)
                        : <p>No users found matching your criteria.</p>;

      // Handles a single user lookup
      } else if (resultData.userById) {
          resultsContent = <UserResult user={resultData.userById} onInviteClick={onInviteClick} />;

      // Handles a successful user creation or update
      } else if (resultData.createUser || resultData.updateUser || resultData.addSkillsToUser) {
                    const user = resultData.createUser || resultData.updateUser || resultData.addSkillsToUser;
                    resultsContent = (
                        <div>
                            <p>✅ Success! User profile updated:</p>
                            <UserResult user={user} onInviteClick={onInviteClick} />
                        </div>
                    );
      }
  }
  
  // Fallback for successful operations that don't return a known data structure
  if (!resultsContent && rawJson?.data) {
      resultsContent = <p>✅ The operation was successful. View details for the raw response.</p>;
  // Fallback for GraphQL errors
  } else if (!resultsContent && rawJson?.errors) {
      resultsContent = <p>❌ An error occurred. See details for more information.</p>;
  }

  return (
    <div className="results-display">
      <div className="results-summary">
        {resultsContent}
      </div>
      
      <div className="details-toggle">
        <button onClick={() => setDetailsVisible(!detailsVisible)}>
          {detailsVisible ? 'Hide GraphQL & JSON' : 'Show GraphQL & JSON'}
        </button>
      </div>

      {detailsVisible && (
        <div className="raw-details">
          <strong>Generated GraphQL:</strong>
          <pre>{rawGql}</pre>
          
          <strong>Result JSON:</strong>
          <pre>{JSON.stringify(rawJson, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

// Helper function to render a status badge
const StatusBadge = ({ status }) => {
    let className = 'item-status';
    if (status === 'Hired') className += ' status-hired';
    else if (status === 'Interviewing' || status === 'interview') className += ' status-interviewing';
    else if (status === 'Rejected') className += ' status-rejected';
    else className += ' status-applied';

    return <span className={className}>{status.charAt(0).toUpperCase() + status.slice(1)}</span>;
};

export default ResultsDisplay;