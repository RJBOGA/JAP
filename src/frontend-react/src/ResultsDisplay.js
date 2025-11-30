// src/frontend-react/src/ResultsDisplay.js
import React, { useState } from 'react';
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
const UserResult = ({ user, onInviteClick }) => (
    <div className="result-item">
        <div className="item-header">
            <span className="item-title">{user.firstName} {user.lastName}</span>
            {user.applicationStatus && <StatusBadge status={user.applicationStatus} />}
            {user.is_us_citizen && <span className="citizen-badge">✅ US Citizen</span>}
            <span className="item-location">{user.city && user.country ? `${user.city}, ${user.country}` : ''}</span>
        </div>
        <div className="item-subtitle">{user.professionalTitle || 'No professional title provided'}</div>
        
        {user.years_of_experience != null && (
            <div className="item-detail">
                <strong>Experience:</strong> {user.years_of_experience} years
            </div>
        )}
        {user.highest_qualification && (
            <div className="item-detail">
                <strong>Qualification:</strong> {user.highest_qualification}
            </div>
        )}

        {user.skills && user.skills.length > 0 && (
            <div className="item-skills">
                {user.skills.map(skill => <span key={skill} className="skill-tag">{skill}</span>)}
            </div>
        )}

        <div className="item-links">
            {user.linkedin_profile && <a href={user.linkedin_profile} target="_blank" rel="noopener noreferrer">LinkedIn</a>}
            {user.portfolio_url && <a href={user.portfolio_url} target="_blank" rel="noopener noreferrer">Portfolio</a>}
        </div>

        {/* --- NEW: Invite Button (Recruiter View) --- */}
        {onInviteClick && user.jobId && user.UserID ? (
             <button 
                 className="action-button invite-button"
                 onClick={() => onInviteClick(
                     user.UserID, 
                     user.jobId,
                     `${user.firstName} ${user.lastName}`,
                     user.jobTitle
                 )}
             >
                 {user.applicationStatus ? `${user.applicationStatus} / Schedule` : 'Schedule Interview'}
             </button>
        ) : null}
        {/* ------------------------------------------ */}
    </div>
);

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


const ResultsDisplay = ({ rawGql, rawJson, onInviteClick }) => {
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