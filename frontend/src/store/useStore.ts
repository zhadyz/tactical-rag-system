import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Message, Settings, Document } from '../types';

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

interface AppStore extends ChatState, DocumentState {
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
      settings: {
        mode: 'simple', // Changed from 'adaptive' - simple mode is 3-5x faster for most queries
        useContext: true,
        streamResponse: true, // Enable streaming by default
        darkMode: false,
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
    }),
    {
      name: 'tactical-rag-store',
      partialize: (state) => ({
        settings: state.settings,
        // Don't persist messages, documents, or loading states
      }),
    }
  )
);

export default useStore;
