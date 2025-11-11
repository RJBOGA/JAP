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
const UserResult = ({ user }) => (
    <div className="result-item">
        <div className="item-header">
            <span className="item-title">{user.firstName} {user.lastName}</span>
            <span className="item-location">{user.city && user.country ? `${user.city}, ${user.country}` : ''}</span>
        </div>
        <div className="item-subtitle">{user.professionalTitle || 'No professional title provided'}</div>
        
        {/* CORRECTED THIS LINE: Use '!= null' instead of 'is not null' */}
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
    </div>
);


const ResultsDisplay = ({ rawGql, rawJson }) => {
  const [detailsVisible, setDetailsVisible] = useState(false);

  let resultsContent = null;
  const resultData = rawJson?.data;

  // Check for different types of data and prepare the display content
  if (resultData) {
      // Handles a list of jobs
      if (resultData.jobs && Array.isArray(resultData.jobs)) {
          resultsContent = resultData.jobs.length > 0
            ? resultData.jobs.map(job => <JobResult key={job.jobId} job={job} />)
            : <p>No jobs found matching your criteria.</p>;
      
      // Handles a list of users
      } else if (resultData.users && Array.isArray(resultData.users)) {
          resultsContent = resultData.users.length > 0
            ? resultData.users.map(user => <UserResult key={user.UserID} user={user} />)
            : <p>No users found matching your criteria.</p>;

      // Handles a single user lookup
      } else if (resultData.userById) {
          resultsContent = <UserResult user={resultData.userById} />;

      // Handles a successful user creation or update
      } else if (resultData.createUser || resultData.updateUser) {
          const user = resultData.createUser || resultData.updateUser;
          resultsContent = (
            <div>
              <p>✅ Success! User profile updated:</p>
              <UserResult user={user} />
            </div>
          );
      }
      // Add more parsers here for other operations like 'apply', 'createJob', etc.
  }
  
  // Fallback for successful operations that don't return a list or known object
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

export default ResultsDisplay;