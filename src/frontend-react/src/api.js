// src/frontend-react/src/api.js
import axios from 'axios';

const API_ENDPOINT = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:8000';

// Create an axios instance
const apiClient = axios.create({
  baseURL: API_ENDPOINT,
});

// Use an interceptor to dynamically add the user's role to every request
apiClient.interceptors.request.use(config => {
  try {
    const sessionJSON = localStorage.getItem('session');
    if (sessionJSON) {
      const session = JSON.parse(sessionJSON);
      const userRole = session.user?.role;
      
      if (userRole) {
        // Add the role to a custom header for our GraphQL endpoint
        config.headers['X-User-Role'] = userRole;
      }
    }
  } catch (e) {
    console.error("Could not parse session data for API interceptor", e);
  }
  return config;
}, error => {
  return Promise.reject(error);
});

export default apiClient;