import { useState } from 'react';
import { CELESTIAL_TYPES, CATEGORY_FILTERS, MESSAGES } from '../utils/constants';

function CelestialSidebar({ 
  objects, 
  selectedObject, 
  setSelectedObject, 
  categoryFilter, 
  setCategoryFilter, 
  loading,
  error
}) {
  // Group objects by category
  const objectsByCategory = objects.reduce((acc, obj) => {
    const category = obj.category || 'unknown';
    if (!acc[category]) acc[category] = [];
    acc[category].push(obj);
    return acc;
  }, {});

  // Get celestial type info
  const getCelestialType = (category) => {
    return CELESTIAL_TYPES[category] || CELESTIAL_TYPES.unknown;
  };

  // Format altitude/azimuth
  const formatCoordinates = (obj) => {
    const alt = obj.altitude_degrees?.toFixed(1) || 0;
    const az = obj.azimuth_degrees?.toFixed(1) || 0;
    return `Alt: ${alt}° • Az: ${az}°`;
  };

  // Format magnitude
  const formatMagnitude = (obj) => {
    const mag = obj.magnitude;
    if (mag === undefined || mag === null) return '';
    return ` • Mag: ${mag}`;
  };

  if (loading) {
    return (
      <div className="sidebar h-full flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="sidebar h-full flex items-center justify-center">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  if (objects.length === 0) {
    return (
      <div className="sidebar h-full flex items-center justify-center">
        <p className="text-text-secondary">{MESSAGES.EMPTY}</p>
      </div>
    );
  }

  return (
    <div className="sidebar h-full">
      {/* Category Filter */}
      <div className="mb-4 pb-4 border-b border-white/10">
        <h3 className="text-sm font-medium text-text-secondary mb-2">Filter by Category</h3>
        <div className="flex gap-2 flex-wrap">
          {CATEGORY_FILTERS.map((filter) => (
            <button
              key={filter.value}
              className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                categoryFilter === filter.value
                  ? 'bg-accent-primary text-white'
                  : 'bg-secondary/50 text-text-secondary hover:bg-secondary/70'
              }`}
              onClick={() => setCategoryFilter(filter.value)}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      {/* Objects List */}
      <div className="space-y-3">
        {Object.entries(objectsByCategory).map(([category, categoryObjects]) => {
          const typeInfo = getCelestialType(category);
          
          // Skip empty categories
          if (categoryObjects.length === 0) return null;
          
          // Only show category if it passes the filter
          if (categoryFilter !== 'all' && category !== categoryFilter) return null;

          return (
            <div key={category} className="mb-2">
              {/* Category Header */}
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{typeInfo.icon}</span>
                <h4 className="text-sm font-medium text-accent-primary">
                  {typeInfo.label}s
                </h4>
              </div>
              
              {/* Objects in this category */}
              <div className="space-y-2">
                {categoryObjects.map((obj) => {
                  const isSelected = selectedObject?.object === obj.object || 
                                   selectedObject?.name === obj.object;
                  
                  return (
                    <div
                      key={obj.object || obj.name}
                      className={`celestial-card celestial-card-${category} ${isSelected ? 'ring-2 ring-accent-primary' : ''}`}
                      onClick={() => setSelectedObject(obj)}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-lg">{typeInfo.icon}</span>
                        <div className="flex-1 min-w-0">
                          <h5 className="font-medium truncate">
                            {obj.object || obj.name}
                          </h5>
                          <p className="text-xs text-text-secondary">
                            {formatCoordinates(obj)}{formatMagnitude(obj)}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer with count */}
      <div className="mt-4 pt-4 border-t border-white/10">
        <p className="text-xs text-text-secondary">
          {objects.length} celestial objects visible
        </p>
      </div>
    </div>
  );
}

export default CelestialSidebar;
