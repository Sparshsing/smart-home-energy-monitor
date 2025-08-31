import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import telemetryService from '../services/telemetryService';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';

const Devices = () => {
  const { token } = useAuth();
  const [devices, setDevices] = useState([]);
  const [summary, setSummary] = useState([]);
  const [loading, setLoading] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [error, setError] = useState('');
  const [summaryError, setSummaryError] = useState('');
  const [interval, setInterval] = useState('7d'); // 1h, 1d, 7d, 1m

  // New state for single device telemetry
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [deviceTelemetry, setDeviceTelemetry] = useState([]);
  const [telemetryLoading, setTelemetryLoading] = useState(false);
  const [telemetryError, setTelemetryError] = useState('');
  
  // State for the inputs, separate from the state that triggers the fetch
  const [telemetryInputParams, setTelemetryInputParams] = useState({
    start: new Date(new Date().setDate(new Date().getDate() - 7)),
    end: new Date(),
    interval: '3h',
  });
  // State that triggers the fetch, updated on button click
  const [telemetryRequestParams, setTelemetryRequestParams] = useState(telemetryInputParams);

  useEffect(() => {
    const loadDevices = async () => {
      if (!token) return;
      setLoading(true);
      setError('');
      try {
        const data = await telemetryService.fetchDevices();
        setDevices(data || []);
      } catch (e) {
        setError(e.message || 'Failed to load devices');
      } finally {
        setLoading(false);
      }
    };
    loadDevices();
  }, [token]);

  useEffect(() => {
    const loadSummary = async () => {
      if (!token) return;

      const end = new Date();
      const start = new Date();
      switch (interval) {
        case '1h':
          start.setHours(start.getHours() - 1);
          break;
        case '1d':
          start.setDate(start.getDate() - 1);
          break;
        case '7d':
          start.setDate(start.getDate() - 7);
          break;
        case '1m':
          start.setMonth(start.getMonth() - 1);
          break;
        default:
          start.setDate(start.getDate() - 7);
      }

      setSummaryLoading(true);
      setSummaryError('');
      try {
        const summaryData = await telemetryService.fetchEnergySummary(start, end);
        setSummary(summaryData || []);
      } catch (e) {
        setSummaryError(e.message || 'Failed to load energy summary');
      } finally {
        setSummaryLoading(false);
      }
    };

    loadSummary();
  }, [token, interval]);

  // Effect to load single device telemetry
  useEffect(() => {
    const loadDeviceTelemetry = async () => {
      if (!token || !selectedDevice) return;

      setTelemetryLoading(true);
      setTelemetryError('');
      try {
        const data = await telemetryService.fetchDeviceTelemetry(
          selectedDevice.id,
          telemetryRequestParams.start,
          telemetryRequestParams.end,
          telemetryRequestParams.interval
        );
        setDeviceTelemetry(data || []);
      } catch (e) {
        setTelemetryError(e.message || 'Failed to load device telemetry');
      } finally {
        setTelemetryLoading(false);
      }
    };
    loadDeviceTelemetry();
  }, [token, selectedDevice, telemetryRequestParams]);


  const intervalOptions = [
    { value: '1h', label: '1 Hour' },
    { value: '1d', label: '1 Day' },
    { value: '7d', label: '7 Days' },
    { value: '1m', label: '1 Month' },
  ];

  const handleDeviceClick = (device) => {
    setSelectedDevice(device);
  };
  
  const handleTelemetryParamChange = (e) => {
    const { name, value } = e.target;
    // When a date input changes, the value is 'YYYY-MM-DD'.
    // new Date('YYYY-MM-DD') parses it as midnight UTC.
    // To treat it as midnight in the user's local timezone, we add 'T00:00:00'.
    const isDate = name === 'start' || name === 'end';
    setTelemetryInputParams(prev => ({
        ...prev,
        [name]: isDate ? new Date(`${value}T00:00:00`) : value
    }));
  };

  const handleTelemetryFetch = () => {
      setTelemetryRequestParams(telemetryInputParams);
  };

  const formatDateForInput = (date) => {
      const d = new Date(date);
      const year = d.getFullYear();
      const month = (d.getMonth() + 1).toString().padStart(2, '0');
      const day = d.getDate().toString().padStart(2, '0');
      return `${year}-${month}-${day}`;
  }

  return (
    <div>
      <h1>Device Dashboard</h1>

      <div style={{ marginBottom: '2rem' }}>
        <h2>Energy Usage Summary (kWh)</h2>
        <p>Click a device name in the list below to see detailed usage.</p>
        <div>
          {intervalOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setInterval(opt.value)}
              disabled={interval === opt.value}
              style={{
                margin: '0 5px',
                padding: '5px 10px',
                cursor: 'pointer',
                backgroundColor: interval === opt.value ? '#007bff' : 'white',
                color: interval === opt.value ? 'white' : 'black',
                border: '1px solid #ccc',
              }}
            >
              {opt.label}
            </button>
          ))}
        </div>
        {summaryLoading && <p>Loading summary...</p>}
        {summaryError && <p style={{ color: 'red' }}>{summaryError}</p>}
        {!summaryLoading && !summaryError &&
          (summary.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart
                layout="vertical"
                data={summary}
                margin={{
                  top: 20,
                  right: 30,
                  left: 100,
                  bottom: 5,
                }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis
                  dataKey="device_name"
                  type="category"
                  tick={{ fontSize: 12, fill: '#007bff' }}
                  onClick={(data) => {
                    const device = devices.find(d => d.name === data.value);
                    if (device) handleDeviceClick(device);
                  }}
                  style={{ cursor: 'pointer' }}
                />
                <Tooltip />
                <Legend />
                <Bar dataKey="total_kwh" fill="#8884d8" name="Total Energy (kWh)" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p>No energy usage data available for the selected period.</p>
          ))}
      </div>

      <hr />

      {selectedDevice && (
        <div style={{ marginTop: '2rem' }}>
          <h2>Telemetry for {selectedDevice.name} (Avg Watts)</h2>
          
          <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center' }}>
            <div>
                <label>Start Date: </label>
                <input 
                    type="date" 
                    name="start" 
                    value={formatDateForInput(telemetryInputParams.start)}
                    onChange={handleTelemetryParamChange}
                />
            </div>
            <div style={{ marginLeft: '1rem' }}>
                <label>End Date: </label>
                <input 
                    type="date" 
                    name="end" 
                    value={formatDateForInput(telemetryInputParams.end)}
                    onChange={handleTelemetryParamChange}
                />
            </div>
            <div style={{ marginLeft: '1rem' }}>
                <label>Interval: </label>
                <input 
                    type="text" 
                    name="interval" 
                    value={telemetryInputParams.interval}
                    onChange={handleTelemetryParamChange}
                    placeholder="e.g., 1h, 5m"
                    style={{ width: '60px' }}
                />
            </div>
            <button 
                onClick={handleTelemetryFetch} 
                style={{ 
                    marginLeft: '1rem',
                    backgroundColor: '#007bff',
                    color: 'white',
                    border: 'none',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    cursor: 'pointer'
                }}
            >
                Go
            </button>
          </div>

          {telemetryLoading && <p>Loading telemetry...</p>}
          {telemetryError && <p style={{ color: 'red' }}>{telemetryError}</p>}
          {!telemetryLoading && !telemetryError &&
            (deviceTelemetry.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={deviceTelemetry}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                            dataKey="bucket" 
                            tickFormatter={(timeStr) => new Date(timeStr).toLocaleString()}
                        />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="avg_watts" stroke="#82ca9d" name="Avg Watts" />
                    </LineChart>
                </ResponsiveContainer>
            ) : (
                <p>No detailed telemetry data available for the selected period.</p>
            ))
          }
        </div>
      )}
    </div>
  );
};

export default Devices;


