import { useState } from 'react';
import { MESSAGES, ACTIONS } from '../utils/constants';

function StoryPanel({ object, storyData, loading, error, coordinates, onQuickAction }) {
  const [activeTab, setActiveTab] = useState('details');

  // Extract data from story response (handles both nested .context and flat history)
  const response = storyData?.response || '';
  const skyData = storyData?.data?.sky || {};
  const rawHistory = storyData?.data?.history || {};
  const historyData = rawHistory.context || rawHistory;
  const isVisible = storyData?.data?.is_visible;

  // Format object info
  const formatObjectInfo = () => {
    if (!object) return '';

    const parts = [];
    parts.push(`## 🌌 ${object.object || object.name}`);
    parts.push('');

    if (skyData.observer) {
      const obs = skyData.observer;
      parts.push(`**Location:** Latitude ${obs.latitude}°, Longitude ${obs.longitude}°`);
      parts.push(`**Time:** ${obs.time_utc || 'Now'}`);
      parts.push('');
    }

    if (isVisible !== undefined && isVisible !== null) {
      parts.push(`**Visibility:** ${isVisible ? '✅ Currently visible' : '❌ Not currently visible'}`);
      parts.push('');
    }

    if (object.altitude_degrees !== undefined) {
      parts.push(`**Position:** Altitude ${object.altitude_degrees.toFixed(1)}°, ` +
                `Azimuth ${object.azimuth_degrees.toFixed(1)}°`);
      parts.push('');
    }

    return parts.join('\n');
  };

  // Format history info
  const formatHistoryInfo = () => {
    if (!historyData || typeof historyData !== 'object') return '';

    const parts = [];
    parts.push('## 🚀 Human Exploration History');
    parts.push('');

    if (historyData.missions && historyData.missions.length > 0) {
      parts.push('### Space Missions:');
      historyData.missions.slice(0, 5).forEach(m => {
        const date = m.launch_date || 'Unknown date';
        parts.push(`- **${m.name}** (Launched: ${date})`);
      });
      parts.push('');
    }

    if (historyData.spacecraft && historyData.spacecraft.length > 0) {
      parts.push('### Spacecraft:');
      historyData.spacecraft.slice(0, 5).forEach(s => {
        parts.push(`- **${s.name}** (${s.type || 'Unknown type'})`);
      });
      parts.push('');
    }

    if (historyData.organizations && historyData.organizations.length > 0) {
      parts.push('### Organizations:');
      historyData.organizations.slice(0, 5).forEach(o => {
        parts.push(`- **${o.name}** (${o.country || 'Unknown country'})`);
      });
      parts.push('');
    }

    if (parts.length === 2) {
      parts.push('No direct space missions recorded for this object.');
    }

    return parts.join('\n');
  };

  // Format AI narration
  const formatNarration = () => {
    if (!response) return '';
    return response;
  };

  // Quick actions mapped to target tab
  const quickActions = [
    { label: 'Get Visible Objects', action: ACTIONS.GET_VISIBLE_OBJECTS, targetTab: 'narrative' },
    { label: 'Get Object Details', action: ACTIONS.GET_OBJECT_DETAILS, targetTab: 'narrative' },
    { label: 'Get Exploration History', action: ACTIONS.GET_OBJECT_HISTORY, targetTab: 'narrative' },
  ];

  const handleQuickActionClick = (item) => {
    setActiveTab(item.targetTab);
    if (onQuickAction) {
      onQuickAction(item.action);
    }
  };

  if (loading) {
    return (
      <div className="story-panel h-full flex items-center justify-center flex-col">
        <div className="spinner"></div>
        <p className="mt-4 text-text-secondary">{MESSAGES.LOADING}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="story-panel h-full flex items-center justify-center">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  if (!object) {
    return (
      <div className="story-panel h-full flex items-center justify-center">
        <p className="text-text-secondary">{MESSAGES.SELECT_OBJECT}</p>
      </div>
    );
  }

  return (
    <div className="story-panel h-full flex flex-col">
      {/* Header */}
      <div className="mb-4 pb-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="text-2xl">📜</div>
          <h2 className="text-lg font-bold text-accent-primary">
            {object.object || object.name}
          </h2>
        </div>
        <p className="text-sm text-text-secondary mt-1">
          Lat: {coordinates.lat.toFixed(4)}°, Lon: {coordinates.lon.toFixed(4)}°
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        <button
          className={`px-4 py-2 rounded-lg text-sm transition-colors ${
            activeTab === 'details'
              ? 'bg-accent-primary text-white'
              : 'bg-secondary/50 text-text-secondary hover:bg-secondary/70'
          }`}
          onClick={() => setActiveTab('details')}
        >
          Details
        </button>
        <button
          className={`px-4 py-2 rounded-lg text-sm transition-colors ${
            activeTab === 'history'
              ? 'bg-accent-primary text-white'
              : 'bg-secondary/50 text-text-secondary hover:bg-secondary/70'
          }`}
          onClick={() => setActiveTab('history')}
        >
          History
        </button>
        <button
          className={`px-4 py-2 rounded-lg text-sm transition-colors ${
            activeTab === 'narrative'
              ? 'bg-accent-primary text-white'
              : 'bg-secondary/50 text-text-secondary hover:bg-secondary/70'
          }`}
          onClick={() => setActiveTab('narrative')}
        >
          AI Narration
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto no-scrollbar">
        {activeTab === 'details' && (
          <div className="prose prose-invert max-w-none">
            <div dangerouslySetInnerHTML={{
              __html: formatObjectInfo().replace(/\n/g, '<br />')
            }} />
          </div>
        )}

        {activeTab === 'history' && (
          <div className="prose prose-invert max-w-none">
            <div dangerouslySetInnerHTML={{
              __html: formatHistoryInfo().replace(/\n/g, '<br />')
            }} />
          </div>
        )}

        {activeTab === 'narrative' && (
          <div className="prose prose-invert max-w-none">
            <div dangerouslySetInnerHTML={{
              __html: formatNarration().replace(/\n\n/g, '<br /><br />').replace(/\n/g, '<br />')
            }} />
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="mt-4 pt-4 border-t border-white/10">
        <p className="text-xs text-text-secondary mb-2">Quick Actions:</p>
        <div className="flex gap-2 flex-wrap">
          {quickActions.map((item) => (
            <button
              key={item.action}
              className="btn-secondary text-xs px-3 py-1"
              onClick={() => handleQuickActionClick(item)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default StoryPanel;