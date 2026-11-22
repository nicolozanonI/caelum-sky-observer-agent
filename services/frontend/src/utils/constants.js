// Caelum Frontend Constants

// Predefined cities with coordinates
export const CITIES = [
  { name: 'Rome', lat: 41.9028, lon: 12.4964, country: 'Italy' },
  { name: 'Milan', lat: 45.4642, lon: 9.1900, country: 'Italy' },
  { name: 'Naples', lat: 40.8518, lon: 14.2681, country: 'Italy' },
  { name: 'Paris', lat: 48.8566, lon: 2.3522, country: 'France' },
  { name: 'London', lat: 51.5074, lon: -0.1278, country: 'UK' },
  { name: 'New York', lat: 40.7128, lon: -74.0060, country: 'USA' },
  { name: 'Tokyo', lat: 35.6762, lon: 139.6503, country: 'Japan' },
  { name: 'Moscow', lat: 55.7558, lon: 37.6173, country: 'Russia' },
  { name: 'Berlin', lat: 52.5200, lon: 13.4050, country: 'Germany' },
  { name: 'Madrid', lat: 40.4168, lon: -3.7038, country: 'Spain' },
  { name: 'Sydney', lat: -33.8688, lon: 151.2093, country: 'Australia' },
  { name: 'Los Angeles', lat: 34.0522, lon: -118.2437, country: 'USA' },
];

// Celestial body types and colors
export const CELESTIAL_TYPES = {
  planet: { 
    label: 'Planet', 
    color: '#4f8ef7', 
    icon: '🪐' 
  },
  star: { 
    label: 'Star', 
    color: '#ffd700', 
    icon: '⭐' 
  },
  deep_sky: { 
    label: 'Deep Sky', 
    color: '#8e44ad', 
    icon: '🔭' 
  },
  constellation: { 
    label: 'Constellation', 
    color: '#00d4ff', 
    icon: '🌌' 
  },
  natural_satellite: { 
    label: 'Moon', 
    color: '#f0f0f0', 
    icon: '🌕' 
  },
};

// Available actions
export const ACTIONS = {
  GET_VISIBLE_OBJECTS: 'get_visible_objects',
  GET_OBJECT_DETAILS: 'get_object_details',
  GET_OBJECT_HISTORY: 'get_object_history',
};

// Action labels
export const ACTION_LABELS = {
  [ACTIONS.GET_VISIBLE_OBJECTS]: 'Get Visible Objects',
  [ACTIONS.GET_OBJECT_DETAILS]: 'Get Object Details',
  [ACTIONS.GET_OBJECT_HISTORY]: 'Get Exploration History',
};

// Default coordinates (Rome)
export const DEFAULT_COORDINATES = {
  lat: 41.9028,
  lon: 12.4964,
};

// API endpoints
export const API_ENDPOINTS = {
  VISIBLE_OBJECTS: '/api/v1/sky/view',
  AGENT_ACTION: '/api/v1/sky/action',
  CATALOG: '/api/v1/sky/catalog',
  CONTEXT: (objectName) => `/api/v1/sky/context/${objectName}`,
  MISSIONS: (objectName) => `/api/v1/sky/missions/${objectName}`,
  BODIES: '/api/v1/sky/bodies',
  HEALTH: '/health',
};

// Time presets
export const TIME_PRESETS = [
  { label: 'Now', value: null },
  { label: 'Tonight 9 PM', value: '21:00' },
  { label: 'Tonight 10 PM', value: '22:00' },
  { label: 'Tonight 11 PM', value: '23:00' },
  { label: 'Tomorrow Sunrise', value: '06:00' },
];

// Celestial body categories for filtering
export const CATEGORY_FILTERS = [
  { label: 'All', value: 'all' },
  { label: 'Planets', value: 'planet' },
  { label: 'Stars', value: 'star' },
  { label: 'Deep Sky', value: 'deep_sky' },
  { label: 'Constellations', value: 'constellation' },
];

// Animation settings
export const ANIMATION = {
  FLOAT_DURATION: 3000,
  ORBIT_DURATION: 20000,
  PULSE_DURATION: 4000,
};

// Message constants
export const MESSAGES = {
  LOADING: 'Loading celestial data...',
  EMPTY: 'No celestial objects visible from your location.',
  ERROR: 'Error loading data. Please try again.',
  SELECT_LOCATION: 'Select a location to see the night sky.',
  SELECT_OBJECT: 'Select a celestial object to learn more.',
};
