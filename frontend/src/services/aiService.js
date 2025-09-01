import axios from 'axios';

const AI_API_URL = import.meta.env.VITE_AI_API_URL || 'http://localhost:8003/api/ai';

const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
};

export const query = async (userQuery) => {
  try {
    const response = await axios.post(
      `${AI_API_URL}/query?user_query=${encodeURIComponent(userQuery)}`,
      {},
      {
        headers: {
          ...getAuthHeader(),
        },
      }
    );
    return response.data;
  } catch (error) {
    const message = error.response?.data?.detail || 'Failed to get answer from AI service.';
    throw new Error(message);
  }
};

const aiService = {
  query,
};

export default aiService;
