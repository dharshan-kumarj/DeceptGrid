import { useState, useEffect } from 'react';
import { API } from '../constants/api.ts';

/**
 * Custom hook for auto-refreshing attack logs
 * Person C - Provides real-time log updates for live demo
 */

export const useAttackLogs = (refreshInterval = 2500) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const fetchLogs = async () => {
      try {
        const response = await fetch(API.ATTACK_LOGS + '?limit=20');
        if (response.ok) {
          const data = await response.json();
          if (isMounted) {
            setLogs(data.logs || []);
            setError(null);
          }
        } else {
          if (isMounted) {
            setError('Failed to fetch logs');
          }
        }
      } catch (err) {
        if (isMounted) {
          setError('Network error');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    // Initial fetch
    fetchLogs();

    // Set up interval for auto-refresh
    const interval = setInterval(fetchLogs, refreshInterval);

    // Cleanup
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [refreshInterval]);

  return { logs, loading, error };
};

/**
 * Custom hook for auto-refreshing honeypot logs (Person A's endpoints)
 * For integration with Person B's dashboard
 */
export const useHoneypotLogs = (refreshInterval = 2500) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const fetchLogs = async () => {
      try {
        const response = await fetch(API.HONEYPOT_LOGS);
        if (response.ok) {
          const data = await response.json();
          if (isMounted) {
            setLogs(data.logs || data || []); // Handle different response formats
            setError(null);
          }
        } else {
          if (isMounted) {
            setError('Failed to fetch honeypot logs');
          }
        }
      } catch (err) {
        if (isMounted) {
          setError('Network error');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    // Initial fetch
    fetchLogs();

    // Set up interval for auto-refresh
    const interval = setInterval(fetchLogs, refreshInterval);

    // Cleanup
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [refreshInterval]);

  return { logs, loading, error };
};

/**
 * Custom hook for real-time meter status (Person B's endpoints)
 */
export const useMeterStatus = (refreshInterval = 5000) => {
  const [meterData, setMeterData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const fetchMeterStatus = async () => {
      try {
        const response = await fetch(API.METER_STATUS);
        if (response.ok) {
          const data = await response.json();
          if (isMounted) {
            setMeterData(data);
            setError(null);
          }
        } else {
          if (isMounted) {
            setError('Failed to fetch meter status');
          }
        }
      } catch (err) {
        if (isMounted) {
          setError('Network error');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    // Initial fetch
    fetchMeterStatus();

    // Set up interval for auto-refresh
    const interval = setInterval(fetchMeterStatus, refreshInterval);

    // Cleanup
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [refreshInterval]);

  return { meterData, loading, error };
};

export default { useAttackLogs, useHoneypotLogs, useMeterStatus };