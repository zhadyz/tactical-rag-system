'use client'

import React, { useRef, useState, Suspense } from 'react'
import { Canvas, useFrame, ThreeEvent } from '@react-three/fiber'
import { OrbitControls, useGLTF, Environment, Html } from '@react-three/drei'
import { motion, AnimatePresence } from 'motion/react'
import * as THREE from 'three'

// GPU Architecture Info
interface GPUComponentInfo {
  id: string
  title: string
  description: string
  specs: string[]
  position: [number, number, number]
  color: string
}

const gpuComponents: GPUComponentInfo[] = [
  {
    id: 'cuda-cores',
    title: 'CUDA Cores',
    description: 'Parallel processing units that execute embedding calculations simultaneously',
    specs: ['16,384 cores', 'FP32 performance', 'Batch processing', 'Vector operations'],
    position: [0, 0, 0.3], // Center of GPU die
    color: '#3b82f6'
  },
  {
    id: 'tensor-cores',
    title: 'Tensor Cores',
    description: 'Specialized AI acceleration units for matrix operations in neural networks',
    specs: ['512 Gen 3 cores', 'Mixed precision', 'FP16/INT8 support', '989 TFLOPS'],
    position: [0, 0, 0.1], // Center of GPU die, slightly lower
    color: '#10b981'
  },
  {
    id: 'vram',
    title: 'HBM3 Memory',
    description: 'High-bandwidth memory for storing embeddings and model weights',
    specs: ['80GB capacity', '3.35 TB/s bandwidth', 'Stack architecture', 'ECC support'],
    position: [-0.6, 0, 0.2], // Left side of motherboard
    color: '#8b5cf6'
  },
  {
    id: 'vrm',
    title: 'Power Delivery',
    description: 'Voltage regulation modules providing stable power for extreme workloads',
    specs: ['700W TDP', '12-phase design', 'Dynamic regulation', 'Efficiency optimized'],
    position: [0.6, 0, 0.2], // Right side near power connector
    color: '#f59e0b'
  }
]

// Hotspot Marker Component
interface HotspotProps {
  component: GPUComponentInfo
  onClick: () => void
  isActive: boolean
}

function Hotspot({ component, onClick, isActive }: HotspotProps) {
  const [hovered, setHovered] = useState(false)

  return (
    <mesh
      position={component.position}
      onClick={onClick}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      <sphereGeometry args={[0.08, 16, 16]} />
      <meshStandardMaterial
        color={component.color}
        emissive={component.color}
        emissiveIntensity={isActive ? 1.5 : hovered ? 1 : 0.5}
        transparent
        opacity={0.8}
      />
      {/* Pulsing ring effect when active or hovered */}
      {(isActive || hovered) && (
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.1, 0.15, 32]} />
          <meshBasicMaterial
            color={component.color}
            transparent
            opacity={0.4}
            side={THREE.DoubleSide}
          />
        </mesh>
      )}
    </mesh>
  )
}

// GPU Model Component - Loads actual RTX 3080 model
interface GPUModelProps {
  clicked: boolean
  setClicked: (clicked: boolean) => void
  onHotspotClick: (componentId: string) => void
  activeHotspot: string | null
}

function GPUModel({ clicked, setClicked, onHotspotClick, activeHotspot }: GPUModelProps) {
  const groupRef = useRef<THREE.Group>(null)
  const fanRefs = useRef<THREE.Object3D[]>([])
  const autoRotationRef = useRef(0)
  const lastInteractionTime = useRef(Date.now())
  const isInteracting = useRef(false)

  // Load the GPU model (you need to download it first from Sketchfab)
  // URL: https://sketchfab.com/3d-models/geforce-rtx-3080-graphics-card-8b947ee1bf7a4e3d8ffa1c24893ac160
  // Place the downloaded .glb file in public/models/geforce_rtx_3080_graphics_card.glb
  const { scene } = useGLTF('/models/geforce_rtx_3080_graphics_card.glb')

  // Find fan blade objects in the model hierarchy (not the ring/housing)
  React.useEffect(() => {
    if (scene) {
      const fans: THREE.Object3D[] = []
      scene.traverse((child) => {
        // Look for fan objects - this model has "fan_RTX_3080_0" and "fan_2_RTX_3080_0"
        const name = child.name.toLowerCase()
        const isFanObject = (
          name.startsWith('fan_') &&
          !name.includes('ring') &&
          !name.includes('holder')
        )

        if (isFanObject && (child as THREE.Mesh).isMesh) {
          fans.push(child)
        }
      })
      fanRefs.current = fans
      console.log(`[GPU Visualizer] Found ${fans.length} fan objects:`, fans.map(f => f.name))
    }
  }, [scene])

  useFrame((state, delta) => {
    if (!groupRef.current) return

    // Auto-rotation around Y-axis (vertical axis) - subtle spin
    const AUTO_ROTATION_SPEED = 0.002 // Very slow, subtle rotation
    const INTERACTION_CHECK_MS = 100 // Check if user stopped interacting (very short)
    const RETURN_DAMPING = 0.08 // Smooth return to auto-rotation speed

    // Always increment auto-rotation angle (continuous time)
    autoRotationRef.current += AUTO_ROTATION_SPEED

    // Check if user recently interacted
    const timeSinceInteraction = Date.now() - lastInteractionTime.current
    const isCurrentlyInteracting = timeSinceInteraction < INTERACTION_CHECK_MS

    if (isCurrentlyInteracting) {
      // User is actively interacting - sync auto-rotation reference to current position
      // This ensures seamless resume when interaction stops
      autoRotationRef.current = groupRef.current.rotation.y
      isInteracting.current = true
    } else {
      // User stopped interacting - smoothly blend back to auto-rotation
      const targetY = autoRotationRef.current
      const currentY = groupRef.current.rotation.y

      // Smooth interpolation (exponential decay) - gradually catches up to auto-rotation
      groupRef.current.rotation.y += (targetY - currentY) * RETURN_DAMPING

      isInteracting.current = false
    }

    // Animate GPU fan blades
    if (fanRefs.current.length > 0) {
      const fanSpeed = 0.05 // Base idle speed
      fanRefs.current.forEach((fan) => {
        // Fans rotate on their local Z-axis (perpendicular to GPU card)
        fan.rotation.z += fanSpeed
      })
    } else {
      // Model loaded but no fans detected - try logging once
      if (scene && !groupRef.current?.userData.loggedOnce) {
        console.log('[GPU Visualizer] Model loaded but no fan blades found')
        console.log('[GPU Visualizer] All mesh objects:', [])
        scene.traverse((child) => {
          if ((child as THREE.Mesh).isMesh) {
            console.log(`  - ${child.name} (type: ${child.type})`)
          }
        })
        if (groupRef.current) groupRef.current.userData.loggedOnce = true
      }
    }
  })


  return (
    <group
      ref={groupRef}
      scale={0.3}
      rotation={[0, 0, 0]}
      onPointerDown={() => {
        lastInteractionTime.current = Date.now()
      }}
      onPointerMove={(e) => {
        if (e.buttons > 0) {
          lastInteractionTime.current = Date.now()
        }
      }}
      onWheel={() => {
        lastInteractionTime.current = Date.now()
      }}
    >
      <primitive object={scene} />
    </group>
  )
}

// Fallback GPU (simple version while model loads or if model is missing)
function FallbackGPU() {
  return (
    <group scale={2.5} rotation={[0.1, 0, 0]}>
      <mesh>
        <boxGeometry args={[4, 0.4, 2.5]} />
        <meshStandardMaterial color="#1a1a1a" metalness={0.8} roughness={0.2} />
      </mesh>
      <mesh position={[0, 0.25, 0]}>
        <boxGeometry args={[3.8, 0.3, 2.3]} />
        <meshStandardMaterial color="#2a2a2a" metalness={0.9} roughness={0.1} />
      </mesh>
    </group>
  )
}

// Stats Display Component
interface Stat {
  label: string
  value: string
  color: string
}

const gpuStats: Stat[] = [
  { label: 'CUDA Cores', value: '16,384', color: '#3b82f6' },
  { label: 'Tensor Cores', value: '512', color: '#10b981' },
  { label: 'VRAM', value: '80GB HBM3', color: '#8b5cf6' },
  { label: 'Memory BW', value: '3.35 TB/s', color: '#f59e0b' },
  { label: 'FP16 Performance', value: '989 TFLOPS', color: '#ec4899' },
  { label: 'Power', value: '700W TDP', color: '#ef4444' }
]

export function GPUVisualizer() {
  const [selectedStat, setSelectedStat] = useState<number | null>(null)
  const [activeHotspot, setActiveHotspot] = useState<string | null>(null)

  const selectedComponent = activeHotspot
    ? gpuComponents.find(c => c.id === activeHotspot)
    : null

  return (
    <div className="relative w-full">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="mb-8 text-center"
      >
        <h2 className="mb-4 text-4xl font-bold text-gray-900 dark:text-white md:text-5xl">
          Powered by <span className="text-[#76B900]">NVIDIA™</span>
        </h2>
      </motion.div>

      {/* 3D Canvas */}
      <div className="relative mx-auto aspect-video max-w-5xl overflow-hidden">
        {/* Canvas Container */}
        <Canvas
          camera={{ position: [0, 1.5, 12], fov: 50 }}
          gl={{ antialias: true, alpha: true }}
        >
          {/* Lighting */}
          <ambientLight intensity={0.5} />
          <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1} />
          <pointLight position={[-10, -10, -10]} intensity={0.5} color="#3b82f6" />

          {/* Environment Map for Reflections */}
          <Environment preset="city" />

          {/* GPU Model with Suspense fallback */}
          <Suspense fallback={<FallbackGPU />}>
            <GPUModel
              clicked={false}
              setClicked={() => {}}
              onHotspotClick={setActiveHotspot}
              activeHotspot={activeHotspot}
            />
          </Suspense>

          {/* Camera Controls - Sketchfab-like smooth interactions */}
          <OrbitControls
            enableZoom={true}
            enablePan={true}
            enableDamping={true}
            dampingFactor={0.05}
            rotateSpeed={0.5}
            zoomSpeed={0.8}
            minDistance={3}
            maxDistance={15}
            minPolarAngle={0}
            maxPolarAngle={Math.PI}
            autoRotate={false}
          />
        </Canvas>
      </div>

      {/* GPU Stats Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3"
      >
        {gpuStats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.3 + index * 0.1 }}
            onHoverStart={() => setSelectedStat(index)}
            onHoverEnd={() => setSelectedStat(null)}
            className="group relative cursor-pointer overflow-hidden rounded-2xl border border-gray-200/30 bg-white/40 p-6 backdrop-blur-xl transition-all hover:scale-105 dark:border-gray-700/30 dark:bg-gray-900/40"
            style={{
              boxShadow: selectedStat === index
                ? `0 20px 60px -15px ${stat.color}30, 0 0 0 1px ${stat.color}40`
                : 'none'
            }}
          >
            {/* Glow Effect on Hover */}
            {selectedStat === index && (
              <motion.div
                layoutId="stat-glow"
                className="absolute inset-0 opacity-20"
                style={{
                  background: `radial-gradient(circle at 50% 50%, ${stat.color}, transparent 70%)`
                }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              />
            )}

            <div className="relative">
              <div
                className="mb-2 inline-flex rounded-lg px-2 py-1 text-xs font-semibold uppercase tracking-wide"
                style={{
                  backgroundColor: `${stat.color}20`,
                  color: stat.color
                }}
              >
                {stat.label}
              </div>
              <div className="text-3xl font-bold text-gray-900 dark:text-white">
                {stat.value}
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Component Details Panel */}
      <AnimatePresence mode="wait">
        {selectedComponent && (
          <motion.div
            key={selectedComponent.id}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            transition={{ duration: 0.4 }}
            className="mt-8 overflow-hidden rounded-3xl border p-8 shadow-2xl backdrop-blur-xl"
            style={{
              borderColor: `${selectedComponent.color}40`,
              background: `linear-gradient(135deg, ${selectedComponent.color}10, ${selectedComponent.color}05)`,
              boxShadow: `0 20px 60px -15px ${selectedComponent.color}30`
            }}
          >
            <div className="flex items-start gap-6">
              <div
                className="rounded-2xl p-4"
                style={{ backgroundColor: `${selectedComponent.color}20` }}
              >
                <div
                  className="h-12 w-12 rounded-full"
                  style={{ backgroundColor: selectedComponent.color }}
                />
              </div>
              <div className="flex-1">
                <h3 className="mb-2 text-2xl font-bold text-gray-900 dark:text-white">
                  {selectedComponent.title}
                </h3>
                <p className="mb-6 text-gray-600 dark:text-gray-400">
                  {selectedComponent.description}
                </p>
                <div className="grid gap-3 md:grid-cols-2">
                  {selectedComponent.specs.map((spec, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-center gap-2"
                    >
                      <div
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: selectedComponent.color }}
                      />
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {spec}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Performance Impact */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.8 }}
        className="mt-8 rounded-3xl border border-blue-500/30 bg-gradient-to-br from-blue-50/80 to-blue-100/50 p-8 backdrop-blur-xl dark:from-blue-950/30 dark:to-blue-900/20"
      >
        <h3 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
          Performance Impact
        </h3>
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <div className="mb-1 text-sm font-medium text-gray-600 dark:text-gray-400">
              Embedding Speed
            </div>
            <div className="text-3xl font-bold text-green-600 dark:text-green-400">
              10x faster
            </div>
          </div>
          <div>
            <div className="mb-1 text-sm font-medium text-gray-600 dark:text-gray-400">
              Inference Latency
            </div>
            <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
              2-3s → 200ms
            </div>
          </div>
          <div>
            <div className="mb-1 text-sm font-medium text-gray-600 dark:text-gray-400">
              Throughput
            </div>
            <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
              1200 docs/s
            </div>
          </div>
        </div>
      </motion.div>

      {/* Attribution */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 1 }}
        className="mt-4 text-center text-xs text-gray-500 dark:text-gray-600"
      >
        GPU 3D Model: "GeForce RTX 3080 Graphics Card" by{' '}
        <a
          href="https://sketchfab.com/samuelsurovic"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-gray-700 dark:hover:text-gray-400"
        >
          _surovic_
        </a>
        {' '}licensed under{' '}
        <a
          href="https://creativecommons.org/licenses/by/4.0/"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-gray-700 dark:hover:text-gray-400"
        >
          CC Attribution
        </a>
      </motion.div>
    </div>
  )
}
