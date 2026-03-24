import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Message, Settings, Document, AgentStep, RetrievalStage, CRAGEvaluation, VerificationResult } from '../types';

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  conversationId: string | null;
}

interface DocumentState {
  documents: Document[];
  isUploading: boolean;
}

interface AgentState {
  currentSteps: AgentStep[];
  retrievalStages: RetrievalStage[];
  cragEvaluations: CRAGEvaluation[];
  verificationResults: VerificationResult[];
  isAgentActive: boolean;
}

interface AppStore extends ChatState, DocumentState, AgentState {
  settings: Settings;

  // Chat actions
  addMessage: (message: Message) => void;
  updateLastMessage: (content: string, sources?: any[], metadata?: any) => void;
  appendToLastMessage: (content: string) => void;
  setLastMessageStreaming: (isStreaming: boolean) => void;
  setLoading: (loading: boolean) => void;
  setStreaming: (streaming: boolean) => void;
  setError: (error: string | null) => void;
  clearChat: () => void;
  setConversationId: (id: string | null) => void;

  // Settings actions
  updateSettings: (settings: Partial<Settings>) => void;
  toggleDarkMode: () => void;

  // Document actions
  addDocument: (doc: Document) => void;
  updateDocument: (id: string, updates: Partial<Document>) => void;
  removeDocument: (id: string) => void;
  setUploading: (uploading: boolean) => void;

  // Agent actions
  addAgentStep: (step: AgentStep) => void;
  updateAgentStep: (stepId: string, updates: Partial<AgentStep>) => void;
  setRetrievalStages: (stages: RetrievalStage[]) => void;
  setCRAGEvaluations: (evaluations: CRAGEvaluation[]) => void;
  setVerificationResults: (results: VerificationResult[]) => void;
  setAgentActive: (active: boolean) => void;
  clearAgentState: () => void;
  finalizeAgentMessage: () => void;
}

const useStore = create<AppStore>()(
  persist(
    (set) => ({
      // Initial state
      messages: [],
      isLoading: false,
      isStreaming: false,
      error: null,
      conversationId: null,
      documents: [],
      isUploading: false,

      // Agent state
      currentSteps: [],
      retrievalStages: [],
      cragEvaluations: [],
      verificationResults: [],
      isAgentActive: false,

      settings: {
        mode: 'direct',
        useContext: true,
        streamResponse: true,
        darkMode: false,
        rerankPreset: 'quality',
        showAgentReasoning: true,
      },

      // Chat actions
      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
          error: null,
        })),

      updateLastMessage: (content, sources, metadata) =>
        set((state) => {
          const messages = [...state.messages];
          const lastMessage = messages[messages.length - 1];

          if (lastMessage && lastMessage.role === 'assistant') {
            lastMessage.content = content;
            if (sources) {
              lastMessage.sources = sources;
            }
            if (metadata) {
              lastMessage.metadata = {
                ...lastMessage.metadata,
                ...metadata,
              };
            }
          }

          return { messages };
        }),

      appendToLastMessage: (content) =>
        set((state) => {
          const messages = [...state.messages];
          const lastMessage = messages[messages.length - 1];

          if (lastMessage && lastMessage.role === 'assistant') {
            lastMessage.content += content;
          }

          return { messages };
        }),

      setLastMessageStreaming: (isStreaming) =>
        set((state) => {
          const messages = [...state.messages];
          const lastMessage = messages[messages.length - 1];

          if (lastMessage && lastMessage.role === 'assistant') {
            lastMessage.isStreaming = isStreaming;
          }

          return { messages };
        }),

      setLoading: (loading) => set({ isLoading: loading }),

      setStreaming: (streaming) => set({ isStreaming: streaming }),

      setError: (error) => set({ error }),

      clearChat: () =>
        set({
          messages: [],
          error: null,
          conversationId: null,
        }),

      setConversationId: (id) => set({ conversationId: id }),

      // Settings actions
      updateSettings: (newSettings) =>
        set((state) => ({
          settings: { ...state.settings, ...newSettings },
        })),

      toggleDarkMode: () =>
        set((state) => {
          const darkMode = !state.settings.darkMode;

          // Update DOM
          if (darkMode) {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }

          return {
            settings: { ...state.settings, darkMode },
          };
        }),

      // Document actions
      addDocument: (doc) =>
        set((state) => ({
          documents: [...state.documents, doc],
        })),

      updateDocument: (id, updates) =>
        set((state) => ({
          documents: state.documents.map((doc) =>
            doc.id === id ? { ...doc, ...updates } : doc
          ),
        })),

      removeDocument: (id) =>
        set((state) => ({
          documents: state.documents.filter((doc) => doc.id !== id),
        })),

      setUploading: (uploading) => set({ isUploading: uploading }),

      // Agent actions
      addAgentStep: (step) =>
        set((state) => ({
          currentSteps: [...state.currentSteps, step],
        })),

      updateAgentStep: (stepId, updates) =>
        set((state) => ({
          currentSteps: state.currentSteps.map((step) =>
            step.id === stepId ? { ...step, ...updates } : step
          ),
        })),

      setRetrievalStages: (stages) => set({ retrievalStages: stages }),

      setCRAGEvaluations: (evaluations) => set({ cragEvaluations: evaluations }),

      setVerificationResults: (results) => set({ verificationResults: results }),

      setAgentActive: (active) => set({ isAgentActive: active }),

      clearAgentState: () =>
        set({
          currentSteps: [],
          retrievalStages: [],
          cragEvaluations: [],
          verificationResults: [],
          isAgentActive: false,
        }),

      finalizeAgentMessage: () =>
        set((state) => {
          const messages = [...state.messages];
          const lastMessage = messages[messages.length - 1];

          if (lastMessage && lastMessage.role === 'assistant') {
            if (state.currentSteps.length > 0) {
              lastMessage.agentSteps = [...state.currentSteps];
            }
            if (state.retrievalStages.length > 0) {
              lastMessage.retrievalStages = [...state.retrievalStages];
            }
            if (state.cragEvaluations.length > 0) {
              lastMessage.cragEvaluations = [...state.cragEvaluations];
            }
            if (state.verificationResults.length > 0) {
              lastMessage.verificationResults = [...state.verificationResults];
            }
          }

          return {
            messages,
            currentSteps: [],
            retrievalStages: [],
            cragEvaluations: [],
            verificationResults: [],
            isAgentActive: false,
          };
        }),
    }),
    {
      name: 'forge-store',
      version: 1,
      partialize: (state) => ({
        settings: state.settings,
      }),
      migrate: (persistedState: any, version: number) => {
        if (version === 0 || !version) {
          // Migrate old mode values
          if (persistedState?.settings?.mode === 'simple') {
            persistedState.settings.mode = 'direct';
          } else if (persistedState?.settings?.mode === 'adaptive') {
            persistedState.settings.mode = 'agentic';
          }
          // Add showAgentReasoning if missing
          if (persistedState?.settings && persistedState.settings.showAgentReasoning === undefined) {
            persistedState.settings.showAgentReasoning = true;
          }
        }
        return persistedState;
      },
    }
  )
);

export default useStore;
