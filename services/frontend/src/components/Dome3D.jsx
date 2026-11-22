import { useState, useRef } from 'react';
import { CELESTIAL_TYPES } from '../utils/constants';

function Dome3D({ objects = [], selectedObject, setSelectedObject }) {
  // Inclinazione iniziale a 30° per vedere subito la tridimensionalità della cupola
  const [rotation, setRotation] = useState({ x: 30, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const startRef = useRef({ x: 0, y: 0, rotX: 30, rotY: 0 });

  const RADIUS = 220;
  const CENTER = 300; // ViewBox 600x600

  // Proiezione 3D -> 2D unificata per pianeti, griglia e punti cardinali
  const projectPoint = (altDeg, azDeg) => {
    const alt = (altDeg * Math.PI) / 180;
    const az = (azDeg * Math.PI) / 180;

    // Azimut 0° = Nord (asse -Z), 90° = Est (+X)
    const x = RADIUS * Math.cos(alt) * Math.sin(az);
    const y = RADIUS * Math.sin(alt);
    const z = -RADIUS * Math.cos(alt) * Math.cos(az);

    const radY = (rotation.y * Math.PI) / 180;
    const radX = (rotation.x * Math.PI) / 180;

    // Rotazione orizzontale (attorno all'asse verticale Y)
    const x1 = x * Math.cos(radY) - z * Math.sin(radY);
    const z1 = x * Math.sin(radY) + z * Math.cos(radY);

    // Rotazione verticale (inclinazione della vista)
    const y2 = y * Math.cos(radX) - z1 * Math.sin(radX);
    const z2 = y * Math.sin(radX) + z1 * Math.cos(radX);

    return {
      x: CENTER + x1,
      y: CENTER - y2, // Sottraiamo perché in SVG Y cresce verso il basso
      z: z2,
      isBack: z2 < 0, // Utile per attenuare ciò che sta "dietro" la cupola
    };
  };

  // Genera i punti SVG per un cerchio di altitudine costante (es. Orizzonte = 0°)
  const buildAltitudeRing = (altDeg) => {
    const points = [];
    for (let az = 0; az <= 360; az += 5) {
      const p = projectPoint(altDeg, az);
      points.push(`${p.x.toFixed(1)},${p.y.toFixed(1)}`);
    }
    return points.join(' ');
  };

  // Genera un arco meridiano da orizzonte a orizzonte passando per lo Zenith
  const buildMeridianArc = (azDeg) => {
    const points = [];
    for (let alt = 0; alt <= 90; alt += 5) {
      const p = projectPoint(alt, azDeg);
      points.push(`${p.x.toFixed(1)},${p.y.toFixed(1)}`);
    }
    return points.join(' ');
  };

  // Gestione trascinamento (Mouse + Touch unificati con Pointer Events)
  const handlePointerDown = (e) => {
    setIsDragging(true);
    startRef.current = {
      x: e.clientX,
      y: e.clientY,
      rotX: rotation.x,
      rotY: rotation.y,
    };
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e) => {
    if (!isDragging) return;
    const dx = e.clientX - startRef.current.x;
    const dy = e.clientY - startRef.current.y;
    setRotation({
      // Limita l'inclinazione verticale tra 5° (vista laterale) e 85° (vista dall'alto)
      x: Math.max(5, Math.min(85, startRef.current.rotX + dy * 0.4)),
      y: (startRef.current.rotY + dx * 0.4) % 360,
    });
  };

  const handlePointerUp = () => setIsDragging(false);

  // Punti di riferimento sulla base
  const centerBase = { x: CENTER, y: CENTER };
  const northEdge = projectPoint(0, 0);
  const zenith = projectPoint(90, 0);

  const cardinals = [
    { label: 'N', az: 0, highlight: true },
    { label: 'NE', az: 45 },
    { label: 'E', az: 90 },
    { label: 'SE', az: 135 },
    { label: 'S', az: 180 },
    { label: 'SO', az: 225 },
    { label: 'O', az: 270 },
    { label: 'NO', az: 315 },
  ];

  // Ordina gli oggetti dal più lontano al più vicino (painter's algorithm)
  const sortedObjects = [...objects]
    .map((obj) => ({
      ...obj,
      proj: projectPoint(obj.altitude_degrees || 0, obj.azimuth_degrees || 0),
    }))
    .sort((a, b) => a.proj.z - b.proj.z);

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center select-none">
      {/* Pulsanti rapidi di orientamento */}
      <div className="absolute top-3 right-3 z-10 flex gap-2">
        <button
          onClick={() => setRotation({ x: 30, y: 0 })}
          className="px-2.5 py-1 text-xs rounded bg-slate-800/80 text-slate-200 border border-slate-700 hover:bg-slate-700"
        >
          Vista 3D (Nord)
        </button>
        <button
          onClick={() => setRotation({ x: 85, y: 0 })}
          className="px-2.5 py-1 text-xs rounded bg-slate-800/80 text-slate-200 border border-slate-700 hover:bg-slate-700"
        >
          Mappa dall&apos;alto
        </button>
      </div>

      <svg
        viewBox="0 0 600 600"
        className="w-full h-full max-w-[600px] max-h-[600px] touch-none"
        style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      >
        {/* 1. Cerchio dell'orizzonte (Altitudine 0°) */}
        <polygon
          points={buildAltitudeRing(0)}
          fill="rgba(56, 189, 248, 0.05)"
          stroke="rgba(56, 189, 248, 0.5)"
          strokeWidth="2"
        />

        {/* 2. Paralleli di altitudine (30° e 60°) */}
        {[30, 60].map((alt) => (
          <polyline
            key={alt}
            points={buildAltitudeRing(alt)}
            fill="none"
            stroke="rgba(148, 163, 184, 0.18)"
            strokeDasharray="4 4"
            strokeWidth="1"
          />
        ))}

        {/* 3. Meridiani principali (N-S, E-O) */}
        {[0, 90, 180, 270].map((az) => (
          <polyline
            key={az}
            points={buildMeridianArc(az)}
            fill="none"
            stroke="rgba(148, 163, 184, 0.22)"
            strokeWidth="1"
          />
        ))}

        {/* 4. Freccia bussola al centro della base che punta verso NORD */}
        <line
          x1={centerBase.x}
          y1={centerBase.y}
          x2={northEdge.x}
          y2={northEdge.y}
          stroke="#ef4444"
          strokeWidth="2.5"
          strokeDasharray="none"
        />
        <circle cx={centerBase.x} cy={centerBase.y} r="4" fill="#94a3b8" />
        <circle cx={northEdge.x} cy={northEdge.y} r="5" fill="#ef4444" />

        {/* 5. Etichette punti cardinali ancorate all'orizzonte */}
        {cardinals.map(({ label, az, highlight }) => {
          const p = projectPoint(0, az);
          return (
            <text
              key={label}
              x={p.x}
              y={p.y}
              dy="4"
              textAnchor="middle"
              fill={highlight ? '#ef4444' : '#94a3b8'}
              fontSize={highlight ? '14' : '11'}
              fontWeight={highlight ? 'bold' : 'normal'}
            >
              {label}
            </text>
          );
        })}

        {/* 6. Punto Zenith in cima alla cupola */}
        <circle cx={zenith.x} cy={zenith.y} r="3" fill="rgba(56, 189, 248, 0.6)" />
        <text
          x={zenith.x}
          y={zenith.y - 8}
          textAnchor="middle"
          fill="rgba(56, 189, 248, 0.7)"
          fontSize="10"
        >
          Zenith (90°)
        </text>

        {/* 7. Corpi celesti + linea verticale di proiezione sull'orizzonte */}
        {sortedObjects.map((obj) => {
          const typeInfo = CELESTIAL_TYPES[obj.category] || CELESTIAL_TYPES.unknown;
          const isSelected =
            selectedObject?.object === obj.object || selectedObject?.name === obj.object;
          const groundProj = projectPoint(0, obj.azimuth_degrees || 0);
          const radius = Math.max(5, 12 - (obj.magnitude || 0));

          return (
            <g
              key={obj.object || obj.name}
              onClick={(e) => {
                e.stopPropagation();
                setSelectedObject(obj);
              }}
              style={{ cursor: 'pointer' }}
            >
              {/* Linea tratteggiata dal pianeta fino all'orizzonte: fa capire subito l'azimut */}
              <line
                x1={obj.proj.x}
                y1={obj.proj.y}
                x2={groundProj.x}
                y2={groundProj.y}
                stroke={isSelected ? typeInfo.color : 'rgba(255,255,255,0.2)'}
                strokeWidth={isSelected ? '1.5' : '1'}
                strokeDasharray="2 3"
              />

              {/* Punto di caduta sull'orizzonte */}
              <circle
                cx={groundProj.x}
                cy={groundProj.y}
                r="2.5"
                fill={isSelected ? typeInfo.color : 'rgba(255,255,255,0.4)'}
              />

              {/* Pianeta / Stella */}
              <circle
                cx={obj.proj.x}
                cy={obj.proj.y}
                r={isSelected ? radius + 3 : radius}
                fill={typeInfo.color}
                stroke={isSelected ? '#ffffff' : 'none'}
                strokeWidth="2"
              />

              {/* Etichetta sempre visibile per pianeti luminosi o selezionati */}
              <text
                x={obj.proj.x}
                y={obj.proj.y - radius - 6}
                textAnchor="middle"
                fill={isSelected ? '#ffffff' : '#cbd5e1'}
                fontSize={isSelected ? '13' : '11'}
                fontWeight={isSelected ? 'bold' : 'normal'}
              >
                {obj.object || obj.name}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Barra informativa inferiore per l'oggetto selezionato */}
      <div className="text-xs text-slate-400 text-center pb-2">
        {selectedObject ? (
          <span>
            <strong className="text-white">{selectedObject.object || selectedObject.name}</strong> —
            Direzione: <strong className="text-sky-400">{Math.round(selectedObject.azimuth_degrees)}°</strong> |
            Altezza sull&apos;orizzonte: <strong className="text-sky-400">{Math.round(selectedObject.altitude_degrees)}°</strong>
          </span>
        ) : (
          'Trascina per ruotare la cupola • Clicca un corpo celeste per leggere le coordinate'
        )}
      </div>
    </div>
  );
}

export default Dome3D;