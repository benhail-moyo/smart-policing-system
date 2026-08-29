"use client";

import { useEffect, useState } from 'react';
import { api } from '@/lib/client';

interface Pattern {
  pattern_type: string;
  incident_ids: number[];
  confidence: number;
  [key: string]: any;
}

interface PatternData {
  serial_crimes: Pattern[];
  crime_sprees: Pattern[];
  repeat_locations: Pattern[];
  geographic_patterns: Pattern[];
}

export default function PatternVisualization() {
  const [patterns, setPatterns] = useState<PatternData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [daysBack, setDaysBack] = useState(30);

  const fetchPatterns = async (days: number) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/patterns/active?days_back=${days}`);
      const data = await response.json();
      if (data && data.patterns) {
        setPatterns(data.patterns);
      } else {
        setPatterns({
          serial_crimes: [],
          crime_sprees: [],
          repeat_locations: [],
          geographic_patterns: [],
        });
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch patterns');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatterns(daysBack);
  }, [daysBack]);

  if (loading) return (
    <div className="flex items-center justify-center p-8">
      <div className="text-gray-600">Loading patterns...</div>
    </div>
  );

  if (error) return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="text-red-800">Error: {error}</div>
    </div>
  );

  if (!patterns) return (
    <div className="text-gray-600 p-4">No patterns detected</div>
  );

  const totalPatterns = 
    (patterns.serial_crimes?.length ?? 0) + 
    (patterns.crime_sprees?.length ?? 0) + 
    (patterns.repeat_locations?.length ?? 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Active Crime Patterns</h2>
        <div className="flex items-center gap-2">
          <label htmlFor="daysBack" className="text-sm text-gray-600">Time period:</label>
          <select
            id="daysBack"
            value={daysBack}
            onChange={(e) => setDaysBack(Number(e.target.value))}
            className="border border-gray-300 rounded px-3 py-1 text-sm"
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
            <option value={60}>60 days</option>
          </select>
        </div>
      </div>

      {totalPatterns === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <div className="text-gray-600">No active patterns detected in the selected time period</div>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <div className="text-sm font-medium text-gray-700">
              Total Active Patterns: {totalPatterns}
            </div>
          </div>

          {/* Serial Crimes */}
          {(patterns.serial_crimes?.length ?? 0) > 0 && (
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-red-800 mb-3 flex items-center gap-2">
                <span className="w-3 h-3 bg-red-600 rounded-full"></span>
                Serial Crimes ({patterns.serial_crimes.length})
              </h3>
              <div className="space-y-2">
                {patterns.serial_crimes.map((pattern, idx) => (
                  <div key={idx} className="bg-red-50 border border-red-200 rounded p-3">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-medium text-red-900">Pattern #{idx + 1}</span>
                      <span className="text-sm bg-red-200 text-red-800 px-2 py-1 rounded">
                        {(pattern.confidence * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm text-gray-700">
                      <div>
                        <span className="font-medium">Incidents:</span> {pattern.incident_count}
                      </div>
                      <div>
                        <span className="font-medium">Category:</span> {pattern.category || 'Unknown'}
                      </div>
                      <div>
                        <span className="font-medium">Time span:</span> {pattern.time_span_hours?.toFixed(1)} hours
                      </div>
                      <div>
                        <span className="font-medium">Geographic spread:</span> {pattern.geographic_spread_km?.toFixed(2)} km
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Crime Sprees */}
          {(patterns.crime_sprees?.length ?? 0) > 0 && (
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-orange-800 mb-3 flex items-center gap-2">
                <span className="w-3 h-3 bg-orange-600 rounded-full"></span>
                Crime Sprees ({patterns.crime_sprees.length})
              </h3>
              <div className="space-y-2">
                {patterns.crime_sprees.map((pattern, idx) => (
                  <div key={idx} className="bg-orange-50 border border-orange-200 rounded p-3">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-medium text-orange-900">Spree #{idx + 1}</span>
                      <span className="text-sm bg-orange-200 text-orange-800 px-2 py-1 rounded">
                        {(pattern.confidence * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm text-gray-700">
                      <div>
                        <span className="font-medium">Incidents:</span> {pattern.incident_count}
                      </div>
                      <div>
                        <span className="font-medium">Incidents/hour:</span> {pattern.incidents_per_hour?.toFixed(2)}
                      </div>
                      <div>
                        <span className="font-medium">Time span:</span> {pattern.time_span_hours?.toFixed(1)} hours
                      </div>
                      <div>
                        <span className="font-medium">Most recent:</span> {pattern.most_recent ? new Date(pattern.most_recent).toLocaleDateString() : 'N/A'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Repeat Locations */}
          {(patterns.repeat_locations?.length ?? 0) > 0 && (
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-yellow-800 mb-3 flex items-center gap-2">
                <span className="w-3 h-3 bg-yellow-600 rounded-full"></span>
                Repeat Locations ({patterns.repeat_locations.length})
              </h3>
              <div className="space-y-2">
                {patterns.repeat_locations.map((pattern, idx) => (
                  <div key={idx} className="bg-yellow-50 border border-yellow-200 rounded p-3">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-medium text-yellow-900">Location #{idx + 1}</span>
                      <span className="text-sm bg-yellow-200 text-yellow-800 px-2 py-1 rounded">
                        {(pattern.confidence * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm text-gray-700">
                      <div>
                        <span className="font-medium">Incidents:</span> {pattern.incident_count}
                      </div>
                      <div>
                        <span className="font-medium">Category:</span> {pattern.category || 'Unknown'}
                      </div>
                      <div>
                        <span className="font-medium">Location:</span> {pattern.location?.lat?.toFixed(4)}, {pattern.location?.lng?.toFixed(4)}
                      </div>
                      <div>
                        <span className="font-medium">Time span:</span> {pattern.time_span_days?.toFixed(1)} days
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Geographic Patterns */}
          {(patterns.geographic_patterns?.length ?? 0) > 0 && (
            <div className="p-4">
              <h3 className="text-lg font-semibold text-blue-800 mb-3 flex items-center gap-2">
                <span className="w-3 h-3 bg-blue-600 rounded-full"></span>
                Geographic Distribution ({patterns.geographic_patterns.length})
              </h3>
              <div className="space-y-2">
                {patterns.geographic_patterns.map((pattern, idx) => (
                  <div key={idx} className="bg-blue-50 border border-blue-200 rounded p-3">
                    <div className="grid grid-cols-2 gap-2 text-sm text-gray-700">
                      <div>
                        <span className="font-medium">Total incidents:</span> {pattern.total_incidents}
                      </div>
                      <div>
                        <span className="font-medium">Geographic spread:</span> {pattern.geographic_spread_km?.toFixed(2)} km
                      </div>
                      <div className="col-span-2">
                        <span className="font-medium">Geographic center:</span> {pattern.geographic_center?.lat?.toFixed(4)}, {pattern.geographic_center?.lng?.toFixed(4)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
