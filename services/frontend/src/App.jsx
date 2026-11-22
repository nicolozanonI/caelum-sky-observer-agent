import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import CelestialSidebar from './components/CelestialSidebar';
import Dome3D from './components/Dome3D';
import StoryPanel from './components/StoryPanel';
import { DEFAULT_COORDINATES, ACTIONS } from './utils/constants';

function App() {
  // State for location
  const [coordinates, setCoordinates] = useState(DEFAULT_COORDINATES);
  const [timestamp, setTimestamp] = useState(null);

  // State for selected object
  const [selectedObject, setSelectedObject] = useState(null);
  const [visibleObjects, setVisibleObjects] = useState([]);

  // State for story/loading
  const [storyData, setStoryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filter state
  const [categoryFilter, setCategoryFilter] = useState('all');

  // Helper to call /api/v1/sky/action for any structured action
  const executeSkyAction = useCallback(async (actionType, targetObject = selectedObject) => {
    setLoading(true);
    setError(null);

    try {
      const body = {
        action: actionType,
        latitude: coordinates.lat,
        longitude: coordinates.lon,
        timestamp: timestamp,
      };

      if (actionType !== ACTIONS.GET_VISIBLE_OBJECTS && targetObject) {
        body.object_name = targetObject.object || targetObject.name;
      }

      const response = await fetch('/api/v1/sky/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`Failed to execute action: ${actionType}`);
      }

      const data = await response.json();
      setStoryData(data);

      // Update visibleObjects ONLY if the agent payload actually includes 3D dome coordinates
      const returnedObjects = data.data?.sky?.visible_objects;
      if (
        actionType === ACTIONS.GET_VISIBLE_OBJECTS &&
        Array.isArray(returnedObjects) &&
        returnedObjects.length > 0 &&
        returnedObjects[0].altitude_degrees !== undefined &&
        returnedObjects[0].azimuth_degrees !== undefined
      ) {
        setVisibleObjects(returnedObjects);
      }
    } catch (err) {
      setError(err.message);
      setStoryData(null);
    } finally {
      setLoading(false);
    }
  }, [coordinates, timestamp, selectedObject]);

  // Fetch visible objects with exact 3D coordinates when location or time changes
  useEffect(() => {
    const fetchVisibleObjects = async () => {
      setLoading(true);
      setError(null);

      try {
        const params = {
          lat: coordinates.lat,
          lon: coordinates.lon,
        };
        if (timestamp) params.timestamp = timestamp;

        const response = await fetch(
          `/api/v1/sky/view?${new URLSearchParams(params).toString()}`
        );

        if (!response.ok) {
          throw new Error('Failed to fetch visible objects');
        }

        const data = await response.json();
        const list = data.data?.visible_objects || data.visible_objects || [];
        setVisibleObjects(list);

        if (list.length > 0 && !selectedObject) {
          setSelectedObject(list[0]);
        }
      } catch (err) {
        setError(err.message);
        setVisibleObjects([]);
      } finally {
        setLoading(false);
      }
    };

    fetchVisibleObjects();
  }, [coordinates, timestamp]);

  // Fetch story data automatically when an object is selected
  useEffect(() => {
    if (!selectedObject) return;
    executeSkyAction(ACTIONS.GET_OBJECT_DETAILS, selectedObject);
  }, [selectedObject, executeSkyAction]);

  const filteredObjects = categoryFilter === 'all'
    ? visibleObjects
    : visibleObjects.filter(obj => obj.category === categoryFilter);

  return (
    <div className="min-h-screen bg-primary text-text-primary flex flex-col">
      <Header
        coordinates={coordinates}
        setCoordinates={setCoordinates}
        timestamp={timestamp}
        setTimestamp={setTimestamp}
      />

      <div className="flex flex-1 overflow-hidden">
        <div className="w-80 flex-shrink-0 border-r border-white/10">
          <CelestialSidebar
            objects={filteredObjects}
            selectedObject={selectedObject}
            setSelectedObject={setSelectedObject}
            categoryFilter={categoryFilter}
            setCategoryFilter={setCategoryFilter}
            loading={loading}
            error={error}
          />
        </div>

        <div className="flex-1 relative overflow-hidden">
          <Dome3D
            objects={visibleObjects}
            selectedObject={selectedObject}
            setSelectedObject={setSelectedObject}
          />
        </div>

        <div className="w-96 flex-shrink-0 border-l border-white/10">
          <StoryPanel
            object={selectedObject}
            storyData={storyData}
            loading={loading}
            error={error}
            coordinates={coordinates}
            onQuickAction={(actionType) => executeSkyAction(actionType, selectedObject)}
          />
        </div>
      </div>
    </div>
  );
}

export default App;