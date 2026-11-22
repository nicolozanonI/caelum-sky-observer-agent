import { useState, useEffect } from 'react';
import { CITIES, DEFAULT_COORDINATES, TIME_PRESETS } from '../utils/constants';

function Header({ coordinates, setCoordinates, timestamp, setTimestamp }) {
  const [city, setCity] = useState(null);
  const [manualLat, setManualLat] = useState(coordinates.lat);
  const [manualLon, setManualLon] = useState(coordinates.lon);
  const [timePreset, setTimePreset] = useState(null);
  const [useCustomLocation, setUseCustomLocation] = useState(false);

  // Sync manual inputs with coordinates
  useEffect(() => {
    setManualLat(coordinates.lat);
    setManualLon(coordinates.lon);
  }, [coordinates]);

  // Find current city based on coordinates
  useEffect(() => {
    const currentCity = CITIES.find(
      c => Math.abs(c.lat - coordinates.lat) < 0.1 && Math.abs(c.lon - coordinates.lon) < 0.1
    );
    setCity(currentCity || null);
  }, [coordinates]);

  // Handle city selection
  const handleCitySelect = (selectedCity) => {
    setCity(selectedCity);
    setCoordinates({ lat: selectedCity.lat, lon: selectedCity.lon });
    setUseCustomLocation(false);
  };

  // Handle manual coordinates
  const handleManualSubmit = (e) => {
    e.preventDefault();
    setCoordinates({ lat: parseFloat(manualLat), lon: parseFloat(manualLon) });
    setCity(null);
  };

  // Handle time preset
  const handleTimePreset = (preset) => {
    setTimePreset(preset);
    setTimestamp(preset.value);
  };

  // Get current time string
  const getCurrentTime = () => {
    if (timestamp) return new Date(timestamp).toLocaleTimeString();
    return new Date().toLocaleTimeString();
  };

  // Get geolocation
  const getGeolocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCoordinates({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          });
          setCity(null);
          setUseCustomLocation(false);
        },
        (error) => {
          console.error('Geolocation error:', error);
          alert('Unable to get your location. Please select manually.');
        }
      );
    } else {
      alert('Geolocation is not supported by your browser.');
    }
  };

  return (
    <header className="header">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="text-2xl">🌌</div>
        <h1 className="text-xl font-bold text-accent-primary">Caelum</h1>
      </div>

      {/* Location Controls */}
      <div className="flex items-center gap-4">
        {/* City Selector */}
        {!useCustomLocation ? (
          <>
            <select
              className="select-field w-48"
              value={city?.name || ''}
              onChange={(e) => {
                const selectedCity = CITIES.find(c => c.name === e.target.value);
                handleCitySelect(selectedCity);
              }}
            >
              <option value="">Select a city...</option>
              {CITIES.map((city) => (
                <option key={city.name} value={city.name}>
                  {city.name} ({city.country})
                </option>
              ))}
            </select>
            
            {/* Custom location toggle */}
            <button
              className="btn-secondary text-sm px-3 py-1"
              onClick={() => setUseCustomLocation(true)}
            >
              Custom
            </button>
          </>
        ) : (
          <form onSubmit={handleManualSubmit} className="flex gap-2">
            <input
              type="number"
              className="input-field w-20"
              value={manualLat}
              onChange={(e) => setManualLat(e.target.value)}
              placeholder="Lat"
              min="-90"
              max="90"
              step="0.0001"
            />
            <input
              type="number"
              className="input-field w-20"
              value={manualLon}
              onChange={(e) => setManualLon(e.target.value)}
              placeholder="Lon"
              min="-180"
              max="180"
              step="0.0001"
            />
            <button type="submit" className="btn-primary text-sm px-3 py-1">
              Set
            </button>
            <button
              type="button"
              className="btn-secondary text-sm px-3 py-1"
              onClick={() => setUseCustomLocation(false)}
            >
              Cancel
            </button>
          </form>
        )}

        {/* Geolocation Button */}
        <button
          className="btn-secondary text-sm px-3 py-1 flex items-center gap-1"
          onClick={getGeolocation}
          title="Use my location"
        >
          📍 Detect
        </button>

        {/* Time Selector */}
        <select
          className="select-field w-32"
          value={timePreset?.label || 'Now'}
          onChange={(e) => {
            const selected = TIME_PRESETS.find(t => t.label === e.target.value);
            handleTimePreset(selected);
          }}
        >
          {TIME_PRESETS.map((preset) => (
            <option key={preset.label} value={preset.label}>
              {preset.label}
            </option>
          ))}
        </select>

        {/* Current coordinates display */}
        <div className="text-sm text-text-secondary bg-secondary/50 px-3 py-1 rounded-lg">
          Lat: {coordinates.lat.toFixed(4)}°, Lon: {coordinates.lon.toFixed(4)}°
        </div>
      </div>
    </header>
  );
}

export default Header;
