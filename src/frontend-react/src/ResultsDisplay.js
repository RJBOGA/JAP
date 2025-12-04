// src/frontend-react/src/ResultsDisplay.js
import React, { useState } from 'react';
import apiClient from './api'; 
import './ResultsDisplay.css';

// --- NEW COMPONENT: Interview List Card (Manager Dashboard) ---
const InterviewListCard = ({ interview }) => {
    const date = new Date(interview.startTime);
    const dateStr = date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
    const timeStr = date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });

    return (
        <div className="result-item interview-card">
            <div className="item-header">
                <span className="item-title">📅 {dateStr} at {timeStr}</span>
                <span className="item-status status-interviewing">Confirmed</span>
            </div>
            <div className="item-subtitle">
                Candidate: <strong>{interview.candidate?.firstName} {interview.candidate?.lastName}</strong>
            </div>
            <div className="item-company">
                Job: {interview.job?.title} ({interview.job?.company})
            </div>
        </div>
    );
};

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

const UserResult = ({ user, onInviteClick, currentUserRole }) => {
    const [localStatus, setLocalStatus] = useState(user.applicationStatus);
    const [loading, setLoading] = useState(false);

    const status = localStatus ? localStatus.toLowerCase() : '';
    const isScheduled = status.includes('interview') && !status.includes('invite'); // Interviewing
    const isInviteSent = status === 'interviewinvitesent';
    const isHired = status === 'hired';
    const isRejected = status === 'rejected';

    let buttonText = 'Schedule Interview'; // Default manual booking
    if (isInviteSent) buttonText = '📩 Invite Sent';
    if (isScheduled) buttonText = '✅ Interview Scheduled';
    if (isHired) buttonText = '🎉 Hired';
    if (isRejected) buttonText = '❌ Rejected';

    // Format interview time if present
    let interviewDateStr = null;
    let interviewTimeStr = null;
    if (user.interviewTime) {
        try {
            const dt = new Date(user.interviewTime);
            interviewDateStr = dt.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
            interviewTimeStr = dt.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            // ignore formatting errors
        }
    }

    const handleDecision = async (newStatus) => {
        if (!window.confirm(`Mark as ${newStatus}?`)) return;
        setLoading(true);
        try {
            await apiClient.post('/graphql', {
                query: `
                  mutation UpdateStatus($userName: String!, $jobTitle: String!, $newStatus: String!) {
                    updateApplicationStatusByNames(
                      userName: $userName,
                      jobTitle: $jobTitle,
                      newStatus: $newStatus
                    ) { status }
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
            console.error(err);
            alert("Update failed.");
        } finally {
            setLoading(false);
        }
    };

    const isRecruiter = currentUserRole === 'Recruiter';

    return (
        <div className="result-item">
            <div className="item-header">
                <span className="item-title">{user.firstName} {user.lastName}</span>
                {localStatus && <StatusBadge status={localStatus} />} 
                {user.is_us_citizen && <span className="citizen-badge">✅ US Citizen</span>}
                <span className="item-location">{user.city && user.country ? `${user.city}, ${user.country}` : ''}</span>
            </div>
            
            <div className="item-subtitle">{user.professionalTitle || '------------'}</div>
            {user.years_of_experience != null && <div><strong>Experience:</strong> {user.years_of_experience} years</div>}
            
            {user.skills && user.skills.length > 0 && (
                <div className="item-skills">
                    {user.skills.map(skill => <span key={skill} className="skill-tag">{skill}</span>)}
                </div>
            )}

            <div className="item-links">
                {user.resume_url && <a href={`http://localhost:8000${user.resume_url}`} target="_blank" rel="noopener noreferrer" className="resume-link">📄 View Resume</a>}
            </div>

            {isRecruiter && (
                <div className="action-area">
                    {/* Hire/Reject Buttons */}
                    <div className="decision-buttons" style={{marginBottom: '10px'}}>
                         <button className="decision-btn hire-btn" onClick={() => handleDecision("Hired")}>🎉 Hire</button>
                         <button className="decision-btn reject-btn" onClick={() => handleDecision("Rejected")}>❌ Reject</button>
                    </div>
                </div>
            )}

            {/* If interview is scheduled, show the scheduled time for visibility to all roles */}
            {isScheduled && interviewDateStr && (
                <div className="scheduled-time" style={{marginTop: '8px', color: '#444'}}>
                    <small>Scheduled: {interviewDateStr} at {interviewTimeStr}</small>
                </div>
            )}
        </div>
    );
};

// --- UPDATED APPLICATION RESULT: Includes "Select Slot" for Applicant ---
const ApplicationResult = ({ app, onSelectSlotClick, currentUserRole }) => {
    const isInviteSent = app.status === 'InterviewInviteSent';
    const isApplicant = currentUserRole === 'Applicant';

    return (
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
            
            {/* Applicant Self-Scheduling Action: STRICT RBAC */}
            {isInviteSent && isApplicant && (
                <div className="action-area">
                    <p style={{color: '#e65100', fontWeight: 'bold'}}>Action Required: Recruiter has invited you to interview.</p>
                    <button 
                        className="action-button invite-button"
                        onClick={() => onSelectSlotClick(app.candidate?.UserID || app.userId, app.job?.jobId || app.jobId, app.appId, app.job?.title)}
                    >
                        📅 Schedule Now
                    </button>
                </div>
            )}
        </div>
    );
}

const ResultsDisplay = ({ rawGql, rawJson, onInviteClick, currentUserRole }) => {
  const [detailsVisible, setDetailsVisible] = useState(false);

  let resultsContent = null;
  const resultData = rawJson?.data;

  if (resultData) {
      // --- NEW: Manager Dashboard View ---
      if (resultData.myBookedInterviews) {
          resultsContent = (
              <div className="result-group">
                  <h3 className="container-title">My Scheduled Interviews</h3>
                  {resultData.myBookedInterviews.length > 0 ? (
                      resultData.myBookedInterviews.map(interview => <InterviewListCard key={interview.interviewId} interview={interview} />)
                  ) : (
                      <p>No interviews scheduled yet.</p>
                  )}
              </div>
          );
      }
      else if (resultData.applications && Array.isArray(resultData.applications)) {
          // Pass onInviteClick as onSelectSlotClick for Applicant flow (reusing logic in App.js)
          resultsContent = (
              <div className="result-item job-applicant-container">
                  <h3 className="container-title">Your Applications</h3>
                  {resultData.applications.length > 0 ? (
                      resultData.applications.map(app => <ApplicationResult key={app.appId} app={app} onSelectSlotClick={onInviteClick} currentUserRole={currentUserRole} />)
                  ) : (
                      <p>You have not applied to any jobs yet.</p>
                  )}
              </div>
          );
      }
      else if (resultData.updateApplicationStatusByNames || resultData.addNoteToApplicationByJob) {
          const app = resultData.updateApplicationStatusByNames || resultData.addNoteToApplicationByJob;
          resultsContent = <ApplicationResult app={app} currentUserRole={currentUserRole} />;
      }
      else if (resultData.jobs && Array.isArray(resultData.jobs) && resultData.jobs[0]?.applicants) {
          resultsContent = resultData.jobs.map(job => (
              <div key={job.jobId} className="result-item job-applicant-container">
                  <h3 className="container-title">Applicants for: {job.title} at {job.company}</h3>
                      {job.applicants.length > 0 ? (
                      job.applicants.map(applicant => <UserResult key={applicant.UserID} user={{...applicant, jobId: job.jobId, jobTitle: job.title}} onInviteClick={onInviteClick} currentUserRole={currentUserRole} />)
                  ) : (
                      <p>No applicants found for this job yet.</p>
                  )}
              </div>
          ));
      }
      else if (resultData.jobs && Array.isArray(resultData.jobs)) {
          resultsContent = resultData.jobs.length > 0
            ? resultData.jobs.map(job => <JobResult key={job.jobId} job={job} />)
            : <p>No jobs found matching your criteria.</p>;
      } else if (resultData.users && Array.isArray(resultData.users)) {
            resultsContent = resultData.users.length > 0
                ? resultData.users.map(user => <UserResult key={user.UserID} user={user} onInviteClick={onInviteClick} currentUserRole={currentUserRole} />)
                : <p>No users found matching your criteria.</p>;
      } else if (resultData.userById) {
          resultsContent = <UserResult user={resultData.userById} onInviteClick={onInviteClick} currentUserRole={currentUserRole} />;
      }
  }
  
  if (!resultsContent && rawJson?.data) {
      resultsContent = <p>✅ The operation was successful. View details for the raw response.</p>;
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

const StatusBadge = ({ status }) => {
    let className = 'item-status';
    if (status === 'Hired') className += ' status-hired';
    else if (status === 'Interviewing' || status === 'interview') className += ' status-interviewing';
    else if (status === 'InterviewInviteSent') className += ' status-interviewing'; // Orange-ish
    else if (status === 'Rejected') className += ' status-rejected';
    else className += ' status-applied';

    return <span className={className}>{status}</span>;
};

export default ResultsDisplay;