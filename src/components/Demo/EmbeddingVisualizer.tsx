import { useState, useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Line } from '@react-three/drei';
import { motion } from 'framer-motion';
import * as THREE from 'three';
import {
  Sparkles,
  Search,
  Layers,
  ChevronDown,
  Info
} from 'lucide-react';
import type { EmbeddingPoint, EmbeddingSpace } from '../../types/demo';

interface EmbeddingVisualizerProps {
  className?: string;
}

// Sample embedding points (PCA-reduced to 3D)
const generateSampleEmbeddings = (): EmbeddingPoint[] => {
  const sources = ['AFM 200-1', 'Leadership Manual', 'Core Values', 'Doctrine'];
  const points: EmbeddingPoint[] = [];

  for (let i = 0; i < 50; i++) {
    const source = sources[i % sources.length];
    const cluster = i % sources.length;

    points.push({
      id: `point-${i}`,
      position: [
        (Math.random() - 0.5) * 10 + cluster * 3,
        (Math.random() - 0.5) * 10,
        (Math.random() - 0.5) * 10
      ],
      text: `Chunk ${i + 1}: ${source} excerpt`,
      source: source,
      similarity: Math.random(),
      metadata: { chunk: i + 1 }
    });
  }

  return points;
};

export default function EmbeddingVisualizer({ className = '' }: EmbeddingVisualizerProps) {
  const [queryText, setQueryText] = useState('leadership principles');
  const [similarityThreshold, setSimilarityThreshold] = useState(0.7);
  const [colorScheme, setColorScheme] = useState<'source' | 'similarity' | 'cluster'>('similarity');
  const [selectedPoint, setSelectedPoint] = useState<EmbeddingPoint | null>(null);
  const [showConnections, setShowConnections] = useState(true);

  const embeddingSpace = useMemo<EmbeddingSpace>(() => {
    const points = generateSampleEmbeddings();

    // Add query point
    const queryPoint: EmbeddingPoint = {
      id: 'query',
      position: [0, 0, 0],
      text: queryText,
      source: 'Query',
      similarity: 1.0,
      metadata: {}
    };

    return {
      points,
      queryPoint,
      similarityThreshold,
      colorScheme
    };
  }, [queryText, similarityThreshold, colorScheme]);

  const nearestNeighbors = embeddingSpace.points
    .filter(p => p.similarity >= similarityThreshold)
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, 10);

  return (
    <div className={`bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 border border-slate-700 ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-3 bg-gradient-to-br from-pink-500 to-purple-500 rounded-xl">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Embedding Similarity Visualizer</h2>
            <p className="text-slate-400">3D visualization of embedding space</p>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Query Input */}
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
            <Search className="w-4 h-4" />
            Query Text
          </label>
          <input
            type="text"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-pink-500"
            placeholder="Enter query..."
          />
        </div>

        {/* Similarity Threshold */}
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
            <Layers className="w-4 h-4" />
            Similarity Threshold: {similarityThreshold.toFixed(2)}
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={similarityThreshold}
            onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>0.0</span>
            <span>1.0</span>
          </div>
        </div>
      </div>

      {/* Color Scheme & Settings */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex gap-2">
          <span className="text-sm text-slate-400">Color by:</span>
          {(['similarity', 'source', 'cluster'] as const).map((scheme) => (
            <button
              key={scheme}
              onClick={() => setColorScheme(scheme)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                colorScheme === scheme
                  ? 'bg-pink-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {scheme.charAt(0).toUpperCase() + scheme.slice(1)}
            </button>
          ))}
        </div>

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={showConnections}
            onChange={(e) => setShowConnections(e.target.checked)}
            className="w-4 h-4 rounded bg-slate-700 border-slate-600"
          />
          <span className="text-sm text-slate-300">Show connections</span>
        </label>
      </div>

      {/* 3D Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900/50 rounded-xl overflow-hidden border border-slate-700">
          <div className="h-[500px]">
            <Canvas camera={{ position: [15, 15, 15], fov: 50 }}>
              <ambientLight intensity={0.5} />
              <pointLight position={[10, 10, 10]} />
              <OrbitControls enableDamping dampingFactor={0.05} />

              {/* Query Point */}
              {embeddingSpace.queryPoint && (
                <mesh position={embeddingSpace.queryPoint.position as any}>
                  <sphereGeometry args={[0.5, 32, 32]} />
                  <meshStandardMaterial color="#ec4899" emissive="#ec4899" emissiveIntensity={0.5} />
                  <Text
                    position={[0, 0.8, 0]}
                    fontSize={0.3}
                    color="white"
                    anchorX="center"
                    anchorY="middle"
                  >
                    Query
                  </Text>
                </mesh>
              )}

              {/* Embedding Points */}
              {embeddingSpace.points.map((point) => {
                const color = getPointColor(point, colorScheme);
                const isNearby = point.similarity >= similarityThreshold;

                return (
                  <group key={point.id}>
                    <mesh
                      position={point.position as any}
                      onClick={() => setSelectedPoint(point)}
                    >
                      <sphereGeometry args={[isNearby ? 0.3 : 0.2, 16, 16]} />
                      <meshStandardMaterial
                        color={color}
                        opacity={isNearby ? 1 : 0.3}
                        transparent
                      />
                    </mesh>

                    {/* Connection to query */}
                    {showConnections && isNearby && embeddingSpace.queryPoint && (
                      <Line
                        points={[point.position, embeddingSpace.queryPoint.position] as any}
                        color={color}
                        lineWidth={1}
                        opacity={0.3}
                        transparent
                      />
                    )}
                  </group>
                );
              })}

              {/* Grid */}
              <gridHelper args={[20, 20, '#334155', '#1e293b']} />
            </Canvas>
          </div>
        </div>

        {/* Nearest Neighbors List */}
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <h3 className="text-lg font-bold text-white mb-4">
            Nearest Neighbors ({nearestNeighbors.length})
          </h3>
          <div className="space-y-2 max-h-[450px] overflow-y-auto">
            {nearestNeighbors.map((point, idx) => (
              <motion.div
                key={point.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                onClick={() => setSelectedPoint(point)}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedPoint?.id === point.id
                    ? 'bg-pink-500/20 border-pink-500/50'
                    : 'bg-slate-900/50 border-slate-700 hover:border-slate-600'
                }`}
              >
                <div className="flex items-start gap-2">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0 mt-1"
                    style={{ backgroundColor: getPointColor(point, colorScheme) }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-white">#{idx + 1}</span>
                      <span className="text-xs text-slate-400">
                        {(point.similarity * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 line-clamp-2">{point.text}</p>
                    <div className="text-xs text-slate-500 mt-1">{point.source}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Selected Point Details */}
      {selectedPoint && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 bg-pink-500/10 rounded-xl p-4 border border-pink-500/30"
        >
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-pink-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-semibold text-white mb-1">Selected Embedding</h4>
              <p className="text-sm text-slate-300 mb-2">{selectedPoint.text}</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div>
                  <span className="text-slate-400">Source:</span>
                  <div className="text-white font-medium">{selectedPoint.source}</div>
                </div>
                <div>
                  <span className="text-slate-400">Similarity:</span>
                  <div className="text-white font-medium">
                    {(selectedPoint.similarity * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <span className="text-slate-400">Position:</span>
                  <div className="text-white font-medium font-mono">
                    [{selectedPoint.position.map(v => v.toFixed(1)).join(', ')}]
                  </div>
                </div>
                <div>
                  <span className="text-slate-400">Chunk:</span>
                  <div className="text-white font-medium">
                    {selectedPoint.metadata?.chunk || 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Legend */}
      <div className="mt-6 bg-slate-800/50 rounded-xl p-4 border border-slate-700">
        <h4 className="text-sm font-semibold text-slate-300 mb-3">Legend</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-pink-500" />
            <span className="text-sm text-slate-300">Query Point</span>
          </div>
          {colorScheme === 'source' && (
            <>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-blue-500" />
                <span className="text-sm text-slate-300">AFM 200-1</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-green-500" />
                <span className="text-sm text-slate-300">Leadership Manual</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-yellow-500" />
                <span className="text-sm text-slate-300">Core Values</span>
              </div>
            </>
          )}
          {colorScheme === 'similarity' && (
            <div className="flex items-center gap-2">
              <div className="h-4 w-32 rounded bg-gradient-to-r from-blue-500 to-red-500" />
              <span className="text-sm text-slate-300">Low → High</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function getPointColor(point: EmbeddingPoint, colorScheme: 'source' | 'similarity' | 'cluster'): string {
  if (colorScheme === 'similarity') {
    const hue = 240 + (120 * point.similarity); // Blue to green
    return `hsl(${hue}, 70%, 60%)`;
  }

  if (colorScheme === 'source') {
    const colors: Record<string, string> = {
      'AFM 200-1': '#3b82f6',
      'Leadership Manual': '#10b981',
      'Core Values': '#eab308',
      'Doctrine': '#f97316'
    };
    return colors[point.source] || '#94a3b8';
  }

  // Cluster mode
  const hash = point.source.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const hue = (hash * 137.5) % 360;
  return `hsl(${hue}, 70%, 60%)`;
}
