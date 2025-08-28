import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router';
import authService from '../services/authService';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setMessage(''); // Clear previous messages
    try {
      await authService.register(name, email, password);
      navigate('/login');
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (detail) {
        if (Array.isArray(detail)) {
          // Handle FastAPI validation errors (422)
          const invalidFields = detail.map(err => {
            // Capitalize field name from loc array e.g., ["body", "email"]
            if (err.loc && err.loc.length > 1) {
              const field = err.loc[1];
              return field.charAt(0).toUpperCase() + field.slice(1);
            }
            return null;
          }).filter(Boolean).join(', ');

          setMessage(`Invalid fields: ${invalidFields}`);

        } else {
          // Handle other string-based errors (e.g., 400 'Email already registered')
          setMessage(detail);
        }
      } else {
        setMessage('Registration failed. An unexpected error occurred.');
      }
    }
  };

  return (
    <div>
      <h2>Register</h2>
      <form onSubmit={handleRegister}>
        {message && <p className="form-message">{message}</p>}
        <div>
          <label>Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit">Register</button>
      </form>
      <p>
        Already have an account? <Link to="/login">Login here</Link>.
      </p>
    </div>
  );
};

export default Register;
