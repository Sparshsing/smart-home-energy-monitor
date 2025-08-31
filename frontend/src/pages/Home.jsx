import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router';

const Home = () => {
  const { user } = useAuth();

  return (
    <div>
      <h1>Smart Home Energy Monitor</h1>
      {user ? (
        <>
          <p>Hello, {user.name}!</p>
          <p>
            <Link to="/devices">Go to your devices</Link>
          </p>
        </>
      ) : (
        <p>Please log in or register to continue.</p>
      )}
    </div>
  );
};

export default Home;
