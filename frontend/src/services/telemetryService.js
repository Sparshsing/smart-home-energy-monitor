import axios from 'axios';

const TELEMETRY_API_URL = import.meta.env.VITE_TELEMETRY_API_URL || 'http://localhost:8002/api/telemetry';

const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
};

export const fetchDevices = async () => {
  try {
    const response = await axios.get(`${TELEMETRY_API_URL}/devices`, {
      headers: {
        ...getAuthHeader(),
      },
    });
    return response.data;
  } catch (error) {
    const message = error.response?.data?.detail || 'Failed to load devices';
    throw new Error(message);
  }
};

export const fetchEnergySummary = async (start, end) => {
  try {
    const response = await axios.get(`${TELEMETRY_API_URL}/summary`, {
      headers: {
        ...getAuthHeader(),
      },
      params: {
        start: start.toISOString(),
        end: end.toISOString(),
      },
    });
    return response.data;
  } catch (error) {
    const message = error.response?.data?.detail || 'Failed to load energy summary';
    throw new Error(message);
  }
};

export const fetchDeviceTelemetry = async (deviceId, start, end, interval) => {
  try {
    const response = await axios.get(`${TELEMETRY_API_URL}/devices/${deviceId}`, {
      headers: {
        ...getAuthHeader(),
      },
      params: {
        start: start.toISOString(),
        end: end.toISOString(),
        interval,
      },
    });
    return response.data;
  } catch (error) {
    const message = error.response?.data?.detail || 'Failed to load device telemetry';
    throw new Error(message);
  }
};

const telemetryService = {
  fetchDevices,
  fetchEnergySummary,
  fetchDeviceTelemetry,
};

export default telemetryService;


