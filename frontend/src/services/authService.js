import axios from 'axios';

const API_URL = 'http://localhost:8001/api/auth';

const register = async (name, email, password) => {
  const response = await axios.post(`${API_URL}/register`, {
    name,
    email,
    password,
  });
  return response.data;
};

const login = async (email, password) => {
  const params = new URLSearchParams();
  params.append('username', email);
  params.append('password', password);

  const response = await axios.post(`${API_URL}/login`, params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  if (response.data.access_token) {
    localStorage.setItem('token', response.data.access_token);
  }
  
  return response.data;
};

const logout = () => {
    localStorage.removeItem('token');
};

const getCurrentUser = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
        return null;
    }

    try {
        const response = await axios.get(`${API_URL}/users/me`, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        return response.data;
    } catch (error) {
        console.error("Failed to fetch user", error);
        logout(); // Token might be invalid/expired
        return null;
    }
};


const authService = {
  register,
  login,
  logout,
  getCurrentUser,
};

export default authService;
