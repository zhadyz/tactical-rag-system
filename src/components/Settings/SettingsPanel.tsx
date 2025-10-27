import React, { useState, useEffect, useCallback } from 'react';
import { X, Trash2, CheckCircle, Cpu, Zap, Star, Search } from 'lucide-react';
import { ModeSelector } from './ModeSelector';
import { QwenStatus } from '../System/QwenStatus';
import useStore from '../../store/useStore';
import { api } from '../../services/api';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

// PERFORMANCE OPTIMIZATION: Move static data outside component to prevent recreation
const AVAILABLE_MODELS = [
  { id: 'qwen2.5:14b-instruct-q4_K_M', name: 'Qwen2.5 14B (Best Quality)', description: 'Superior reasoning, lower hallucination rate' },
  { id: 'llama3.1:8b', name: 'Llama 3.1 8B (Balanced)', description: 'Fast and reliable for general queries' },
  { id: 'mistral:7b', name: 'Mistral 7B (Fast)', description: 'Lightweight model for quick responses' },
] as const;

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
  isOpen,
  onClose,
}) => {
  const settings = useStore((state) => state.settings);
  const updateSettings = useStore((state) => state.updateSettings);
  const clearChat = useStore((state) => state.clearChat);

  const [isClearing, setIsClearing] = useState(false);
  const [clearSuccess, setClearSuccess] = useState(false);
  const [currentModel, setCurrentModel] = useState<string>('qwen2.5:14b-instruct-q4_K_M');
  const [temperature, setTemperature] = useState<number>(0.0);
  const [isSwitching, setIsSwitching] = useState(false);
  const [isLoadingSettings, setIsLoadingSettings] = useState(true);

  // Load current model from backend
  useEffect(() => {
    const loadCurrentSettings = async () => {
      try {
        setIsLoadingSettings(true);
        const response = await api.getSettings();
        setCurrentModel(response.current_settings.llm_model || 'qwen2.5:14b-instruct-q4_K_M');
        setTemperature(response.current_settings.temperature || 0.0);
      } catch (error) {
        console.error('Failed to load settings:', error);
      } finally {
        setIsLoadingSettings(false);
      }
    };

    if (isOpen) {
      loadCurrentSettings();
    }
  }, [isOpen]);

  // PERFORMANCE OPTIMIZATION: Memoize event handlers
  const handleModelChange = useCallback(async (newModel: string) => {
    setIsSwitching(true);

    try {
      await api.updateSettings({ llm_model: newModel });
      setCurrentModel(newModel);
      clearChat(); // Clear chat after model switch
      alert(`Successfully switched to ${AVAILABLE_MODELS.find(m => m.id === newModel)?.name}`);
    } catch (error) {
      console.error('Failed to switch model:', error);
      alert('Failed to switch model. Please try again.');
    } finally {
      setIsSwitching(false);
    }
  }, [clearChat]);

  const handleTemperatureChange = useCallback(async (newTemp: number) => {
    try {
      await api.updateSettings({ temperature: newTemp });
      setTemperature(newTemp);
    } catch (error) {
      console.error('Failed to update temperature:', error);
    }
  }, []);

  const handleClearCache = useCallback(async () => {
    setIsClearing(true);
    setClearSuccess(false);

    try {
      await api.clearCacheAndMemory();
      clearChat(); // Also clear local chat state

      setClearSuccess(true);
      setTimeout(() => setClearSuccess(false), 3000); // Show success for 3 seconds
    } catch (error) {
      console.error('Failed to clear cache:', error);
      alert('Failed to clear cache. Please try again.');
    } finally {
      setIsClearing(false);
    }
  }, [clearChat]);

  // PERFORMANCE OPTIMIZATION: Memoize toggle handlers
  const handleToggleUseContext = useCallback(() => {
    updateSettings({ useContext: !settings.useContext });
  }, [settings.useContext, updateSettings]);

  const handleToggleStreamResponse = useCallback(() => {
    updateSettings({ streamResponse: !settings.streamResponse });
  }, [settings.streamResponse, updateSettings]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 bottom-0 w-96 bg-white dark:bg-gray-800 shadow-2xl z-50 overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              Settings
            </h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-600 dark:text-gray-400"
              aria-label="Close settings"
            >
              <X size={20} />
            </button>
          </div>

          {/* Settings sections */}
          <div className="space-y-6">
            {/* Query Mode */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Query Mode
              </h3>
              <ModeSelector />
            </div>

            {/* Rerank Preset */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Rerank Quality
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                Balance between speed and answer quality
              </p>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => updateSettings({ rerankPreset: 'quick' })}
                  className={`relative p-3 rounded-lg border-2 transition-all ${
                    settings.rerankPreset === 'quick'
                      ? 'border-primary-600 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                  }`}
                  aria-label="Quick preset - 2 documents"
                  aria-pressed={settings.rerankPreset === 'quick'}
                >
                  <div className="flex flex-col items-center gap-2">
                    <Zap
                      size={20}
                      className={settings.rerankPreset === 'quick' ? 'text-primary-600 dark:text-primary-400' : 'text-gray-500 dark:text-gray-400'}
                    />
                    <div className="text-center">
                      <div className={`text-xs font-semibold ${
                        settings.rerankPreset === 'quick'
                          ? 'text-primary-700 dark:text-primary-300'
                          : 'text-gray-700 dark:text-gray-300'
                      }`}>
                        Quick
                      </div>
                      <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
                        2 docs
                      </div>
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => updateSettings({ rerankPreset: 'quality' })}
                  className={`relative p-3 rounded-lg border-2 transition-all ${
                    settings.rerankPreset === 'quality'
                      ? 'border-primary-600 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                  }`}
                  aria-label="Quality preset - 3 documents (default)"
                  aria-pressed={settings.rerankPreset === 'quality'}
                >
                  <div className="flex flex-col items-center gap-2">
                    <Star
                      size={20}
                      className={settings.rerankPreset === 'quality' ? 'text-primary-600 dark:text-primary-400' : 'text-gray-500 dark:text-gray-400'}
                    />
                    <div className="text-center">
                      <div className={`text-xs font-semibold ${
                        settings.rerankPreset === 'quality'
                          ? 'text-primary-700 dark:text-primary-300'
                          : 'text-gray-700 dark:text-gray-300'
                      }`}>
                        Quality
                      </div>
                      <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
                        3 docs
                      </div>
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => updateSettings({ rerankPreset: 'deep' })}
                  className={`relative p-3 rounded-lg border-2 transition-all ${
                    settings.rerankPreset === 'deep'
                      ? 'border-primary-600 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                  }`}
                  aria-label="Deep preset - 5 documents"
                  aria-pressed={settings.rerankPreset === 'deep'}
                >
                  <div className="flex flex-col items-center gap-2">
                    <Search
                      size={20}
                      className={settings.rerankPreset === 'deep' ? 'text-primary-600 dark:text-primary-400' : 'text-gray-500 dark:text-gray-400'}
                    />
                    <div className="text-center">
                      <div className={`text-xs font-semibold ${
                        settings.rerankPreset === 'deep'
                          ? 'text-primary-700 dark:text-primary-300'
                          : 'text-gray-700 dark:text-gray-300'
                      }`}>
                        Deep
                      </div>
                      <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
                        5 docs
                      </div>
                    </div>
                  </div>
                </button>
              </div>
            </div>

            {/* Query Options */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Query Options
              </h3>
              <div className="space-y-4">
                {/* Use Context */}
                <div className="flex items-center justify-between">
                  <div>
                    <label
                      htmlFor="use-context-panel"
                      className="text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                      Use Context
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Include conversation history in queries
                    </p>
                  </div>
                  <button
                    id="use-context-panel"
                    onClick={handleToggleUseContext}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.useContext
                        ? 'bg-primary-600'
                        : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                    role="switch"
                    aria-checked={settings.useContext}
                    aria-label="Use context in queries"
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        settings.useContext ? 'translate-x-6' : 'translate-x-1'
                      }`}
                      aria-hidden="true"
                    />
                  </button>
                </div>

                {/* Stream Response */}
                <div className="flex items-center justify-between">
                  <div>
                    <label
                      htmlFor="stream-response-panel"
                      className="text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                      Stream Response
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Stream responses in real-time for faster perceived latency
                    </p>
                  </div>
                  <button
                    id="stream-response-panel"
                    onClick={handleToggleStreamResponse}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings.streamResponse
                        ? 'bg-primary-600'
                        : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                    role="switch"
                    aria-checked={settings.streamResponse}
                    aria-label="Stream responses in real-time"
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        settings.streamResponse ? 'translate-x-6' : 'translate-x-1'
                      }`}
                      aria-hidden="true"
                    />
                  </button>
                </div>
              </div>
            </div>

            {/* LLM Model Selection */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
                <Cpu size={16} />
                LLM Model
              </h3>
              <div className="space-y-3">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Choose the language model for generating answers. Switching models clears the cache.
                </p>
                {isLoadingSettings ? (
                  // Loading skeleton for model options
                  <div className="animate-pulse space-y-2">
                    {[1, 2, 3].map((i) => (
                      <div
                        key={i}
                        className="w-full p-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800"
                      >
                        <div className="space-y-2">
                          <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-2/3" />
                          <div className="h-3 bg-gray-300 dark:bg-gray-700 rounded w-full" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-2">
                    {AVAILABLE_MODELS.map((model) => (
                      <button
                        key={model.id}
                        onClick={() => handleModelChange(model.id)}
                        disabled={isSwitching || currentModel === model.id}
                        className={`w-full text-left p-3 rounded-lg border transition-all ${
                          currentModel === model.id
                            ? 'bg-primary-50 dark:bg-primary-900/20 border-primary-300 dark:border-primary-700'
                            : 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800'
                        } ${isSwitching ? 'opacity-50 cursor-not-allowed' : ''}`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                              {model.name}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              {model.description}
                            </div>
                          </div>
                          {currentModel === model.id && (
                            <CheckCircle size={16} className="text-primary-600 dark:text-primary-400 mt-0.5" />
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Qwen Model Status */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Model Installation
              </h3>
              <QwenStatus autoCheck={true} checkInterval={10000} />
            </div>

            {/* Temperature Control */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Temperature
              </h3>
              <div className="space-y-3">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Controls randomness. Lower = more focused, higher = more creative.
                </p>
                {isLoadingSettings ? (
                  // Loading skeleton for temperature slider
                  <div className="animate-pulse">
                    <div className="h-8 bg-gray-300 dark:bg-gray-700 rounded w-full" />
                  </div>
                ) : (
                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min="0"
                      max="2"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => {
                        const newTemp = parseFloat(e.target.value);
                        setTemperature(newTemp);
                      }}
                      onMouseUp={(e) => {
                        const newTemp = parseFloat((e.target as HTMLInputElement).value);
                        handleTemperatureChange(newTemp);
                      }}
                      className="flex-1"
                      disabled={isSwitching}
                      aria-label="Temperature control"
                      aria-valuemin={0}
                      aria-valuemax={2}
                      aria-valuenow={temperature}
                      aria-valuetext={`Temperature ${temperature.toFixed(1)}`}
                    />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300 w-12 text-right" aria-live="polite">
                      {temperature.toFixed(1)}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Clear Cache */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Cache Management
              </h3>
              <div className="space-y-3">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Clear cached responses and conversation memory. Use this if you're seeing
                  outdated answers or want to start fresh.
                </p>
                <button
                  onClick={handleClearCache}
                  disabled={isClearing}
                  className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg border transition-all ${
                    clearSuccess
                      ? 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700 text-green-700 dark:text-green-300'
                      : 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
                  } ${isClearing ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {clearSuccess ? (
                    <>
                      <CheckCircle size={18} />
                      <span className="text-sm font-medium">Cache Cleared!</span>
                    </>
                  ) : (
                    <>
                      <Trash2 size={18} />
                      <span className="text-sm font-medium">
                        {isClearing ? 'Clearing...' : 'Clear Cache & Memory'}
                      </span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* About */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
                About
              </h3>
              <div className="p-4 rounded-lg bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                  <strong>Tactical RAG Desktop</strong>
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Version 4.0.0 (Beta)
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  Intelligent document Q&A powered by advanced retrieval and
                  reasoning techniques.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
