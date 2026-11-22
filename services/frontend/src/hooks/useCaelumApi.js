import { useState, useCallback } from 'react';
import { API_ENDPOINTS, MESSAGES } from '../utils/constants';

/**
 * Custom hook for interacting with Caelum backend API.
 * Provides methods for fetching celestial data with loading, error, and success states.
 */
export function useCaelumApi() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Generic API call handler
   */
  const callApi = useCallback(async (endpoint, method = 'GET', body = null, params = null) => {
    setLoading(true);
    setError(null);
    setData(null);

    try {
      // Build URL with query parameters
      let url = endpoint;
      if (params) {
        const searchParams = new URLSearchParams(params);
        url = `${endpoint}?${searchParams.toString()}`;
      }

      const options = {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
      };

      if (body) {
        options.body = JSON.stringify(body);
      }

      const response = await fetch(url, options);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get visible celestial objects for a location
   */
  const getVisibleObjects = useCallback(async (lat, lon, timestamp = null) => {
    const params = { lat, lon };
    if (timestamp) params.timestamp = timestamp;
    return callApi(API_ENDPOINTS.VISIBLE_OBJECTS, 'GET', null, params);
  }, [callApi]);

  /**
   * Execute a structured agent action
   */
  const executeAgentAction = useCallback(async (action, options = {}) => {
    const body = { action, ...options };
    return callApi(API_ENDPOINTS.AGENT_ACTION, 'POST', body);
  }, [callApi]);

  /**
   * Get celestial catalog
   */
  const getCatalog = useCallback(async (category = null) => {
    let endpoint = API_ENDPOINTS.CATALOG;
    if (category) {
      endpoint = `${API_ENDPOINTS.CATALOG}/${category}`;
    }
    return callApi(endpoint, 'GET');
  }, [callApi]);

  /**
   * Get context/history for a celestial body
   */
  const getContext = useCallback(async (objectName) => {
    return callApi(API_ENDPOINTS.CONTEXT(objectName), 'GET');
  }, [callApi]);

  /**
   * Get mission history for a celestial body
   */
  const getMissions = useCallback(async (objectName, limit = null) => {
    const params = limit ? { limit } : null;
    return callApi(API_ENDPOINTS.MISSIONS(objectName), 'GET', null, params);
  }, [callApi]);

  /**
   * Get all celestial bodies
   */
  const getAllBodies = useCallback(async () => {
    return callApi(API_ENDPOINTS.BODIES, 'GET');
  }, [callApi]);

  /**
   * Check backend health
   */
  const checkHealth = useCallback(async () => {
    return callApi(API_ENDPOINTS.HEALTH, 'GET');
  }, [callApi]);

  /**
   * Combined: Get visible objects + details for a specific object
   */
  const getObjectWithContext = useCallback(async (objectName, lat, lon, timestamp = null) => {
    try {
      // First get visible objects
      const visibleData = await getVisibleObjects(lat, lon, timestamp);
      
      // Check if object is visible
      const visibleObjects = visibleData?.data?.visible_objects || [];
      const isVisible = visibleObjects.some(
        obj => obj.object.toLowerCase() === objectName.toLowerCase()
      );

      // Get object details and history
      const details = await executeAgentAction('get_object_details', {
        object_name: objectName,
        latitude: lat,
        longitude: lon,
        timestamp,
      });

      return {
        visible: isVisible,
        visibleObjects,
        ...details,
      };
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [getVisibleObjects, executeAgentAction]);

  /**
   * Reset states
   */
  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
  }, []);

  return {
    data,
    loading,
    error,
    getVisibleObjects,
    executeAgentAction,
    getCatalog,
    getContext,
    getMissions,
    getAllBodies,
    getObjectWithContext,
    checkHealth,
    reset,
  };
}

export default useCaelumApi;
