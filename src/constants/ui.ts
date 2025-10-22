/**
 * UI Constants
 * Centralized configuration for magic numbers used throughout the application
 */

// PDF Viewer Configuration
export const PDF_VIEWER = {
  MIN_ZOOM: 0.5,
  MAX_ZOOM: 3.0,
  ZOOM_STEP: 0.2,
  DEFAULT_ZOOM: 1.0,
  SCALE_MULTIPLIER: 1.5, // Applied to viewport for rendering
  MAX_HIGHLIGHT_TEXT_LENGTH: 100, // Characters to search for highlighting
} as const;

// Chat Input Configuration
export const CHAT = {
  MAX_MESSAGE_LENGTH: 4000, // Maximum characters per message
  MAX_TEXTAREA_HEIGHT: 200, // Pixels
  MIN_TEXTAREA_HEIGHT: 40, // Pixels
} as const;

// Animation Durations (milliseconds)
export const ANIMATION = {
  FADE_IN: 200,
  SLIDE_UP: 300,
  SCALE_IN: 300,
  PULSE_HIGHLIGHT: 2000,
  BUTTON_PRESS: 150,
  MODAL_TRANSITION: 300,
} as const;

// API Configuration
export const API = {
  DEFAULT_TIMEOUT: 30000, // 30 seconds
  QUERY_TIMEOUT: 60000, // 60 seconds for queries
  HEALTH_CHECK_TIMEOUT: 5000, // 5 seconds for health checks
  MAX_RETRIES: 3,
  RETRY_DELAY_BASE: 1000, // Base delay for exponential backoff
} as const;

// Storage Configuration
export const STORAGE = {
  MAX_ERROR_LOGS: 50,
  MIN_ERROR_LOGS_ON_QUOTA: 10,
  ERROR_LOGS_SIZE_LIMIT: 512 * 1024, // 512KB
} as const;

// Document Upload Configuration
export const DOCUMENT = {
  ACCEPTED_TYPES: ['.pdf', '.txt', '.doc', '.docx', '.md'],
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
} as const;

// Performance Monitoring
export const PERFORMANCE = {
  MAX_QUERY_HISTORY: 100,
  MONITOR_INTERVAL: 5000, // 5 seconds
  RESOURCE_ALERT_THRESHOLD: 90, // Percentage
} as const;

// Z-Index Layers
export const Z_INDEX = {
  MODAL: 50,
  DROPDOWN: 40,
  HEADER: 30,
  OVERLAY: 45,
  TOOLTIP: 60,
} as const;
