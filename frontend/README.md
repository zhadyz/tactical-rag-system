# Tactical RAG Frontend

Modern React/TypeScript frontend for the Tactical RAG project, providing an intuitive chat interface for document Q&A with intelligent retrieval and reasoning.

## Features

- Modern ChatGPT-like UI with clean design
- Real-time message streaming (Coming in Week 2)
- Source citation display with document references
- Dark/Light mode support
- Adaptive and Simple query modes
- Document upload and management
- Responsive mobile-first design
- Type-safe with TypeScript

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Zustand** - State management
- **React Query** - Data fetching (planned)
- **Socket.IO Client** - WebSocket support (Week 2)
- **Radix UI** - Accessible component primitives
- **Lucide React** - Icon library
- **React Markdown** - Markdown rendering

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Start development server
npm run dev
```

The app will be available at http://localhost:3000

### Build for Production

```bash
# Build the app
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/src/
├── components/
│   ├── Chat/
│   │   ├── ChatMessage.tsx      # Individual message bubble
│   │   ├── ChatInput.tsx        # Message input field
│   │   ├── ChatWindow.tsx       # Main chat container
│   │   └── SourceCitation.tsx   # Document source display
│   ├── Documents/
│   │   ├── DocumentUpload.tsx   # File upload UI
│   │   └── DocumentList.tsx     # Uploaded docs list
│   ├── Settings/
│   │   ├── SettingsPanel.tsx    # Settings sidebar
│   │   └── ModeSelector.tsx     # Simple/Adaptive toggle
│   └── Layout/
│       ├── Header.tsx           # Top navigation
│       └── Sidebar.tsx          # Left sidebar
├── hooks/
│   ├── useChat.ts               # Chat state management
│   └── useWebSocket.ts          # WebSocket connection
├── services/
│   └── api.ts                   # API client
├── store/
│   └── useStore.ts              # Zustand store
├── types/
│   └── index.ts                 # TypeScript types
├── App.tsx                      # Main app component
└── main.tsx                     # Entry point
```

## Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=http://localhost:8000
VITE_APP_NAME=Tactical RAG
VITE_APP_VERSION=3.5.0
```

### Vite Proxy

The Vite dev server is configured to proxy API requests to the backend:

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

## API Integration

The frontend communicates with the backend through a REST API:

### Endpoints

- `POST /api/query` - Send a question and get an answer
- `GET /api/health` - Check API health
- `POST /api/documents/upload` - Upload a document
- `GET /api/documents` - List all documents
- `DELETE /api/documents/:id` - Delete a document

### Example Request

```typescript
import { api } from './services/api';

const response = await api.query({
  question: 'What are the main topics?',
  mode: 'adaptive',
  use_context: true,
});
```

## Components

### ChatWindow

Main chat interface with message list and input field.

```tsx
import { ChatWindow } from './components/Chat/ChatWindow';

<ChatWindow />
```

### ChatMessage

Individual message bubble with markdown support and source citations.

```tsx
import { ChatMessage } from './components/Chat/ChatMessage';

<ChatMessage message={message} />
```

### Sidebar

Collapsible sidebar with settings and document management.

```tsx
import { Sidebar } from './components/Layout/Sidebar';

<Sidebar />
```

## State Management

The app uses Zustand for state management with local storage persistence:

```typescript
const useStore = create<AppStore>()(
  persist(
    (set, get) => ({
      messages: [],
      settings: { mode: 'adaptive', useContext: true },
      // ... actions
    }),
    { name: 'tactical-rag-store' }
  )
);
```

## Styling

### Tailwind CSS

The project uses Tailwind CSS with a custom theme:

- Primary color: Blue
- Success color: Green
- Error color: Red
- Dark mode support via `dark:` prefix

### Custom Classes

```css
.btn-primary     /* Primary button */
.btn-secondary   /* Secondary button */
.input-field     /* Form input */
.card            /* Card container */
```

## Development

### Running Tests

```bash
npm run test
```

### Linting

```bash
npm run lint
```

### Type Checking

```bash
npm run type-check
```

## Week 2 Roadmap

- WebSocket integration for streaming responses
- Enhanced document viewer
- Conversation history management
- Export chat functionality
- Advanced settings panel

## Contributing

This is part of the Tactical RAG project. See the main project README for contribution guidelines.

## License

MIT
