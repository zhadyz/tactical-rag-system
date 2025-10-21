import { useEffect, useState } from 'react';
import { ChatWindow } from './components/Chat/ChatWindow';
import { Sidebar } from './components/Layout/Sidebar';
import { Header } from './components/Layout/Header';
import { SettingsPanel } from './components/Settings/SettingsPanel';
import { ErrorBoundary } from './components/ErrorBoundary/ErrorBoundary';
// import { SystemHealthIndicator } from './components/System/SystemHealthIndicator';
import useStore from './store/useStore';

function App() {
  const darkMode = useStore((state) => state.settings.darkMode);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Apply dark mode class to document on mount and when darkMode changes
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  return (
    <ErrorBoundary componentName="App">
      <div className="flex h-screen bg-neutral-50 dark:bg-neutral-950 antialiased">
        {/* Sidebar */}
        <ErrorBoundary componentName="Sidebar">
          <Sidebar />
        </ErrorBoundary>

        {/* Main content area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <ErrorBoundary componentName="Header">
            <Header onOpenSettings={() => setSettingsOpen(true)} />
          </ErrorBoundary>

          {/* Chat window */}
          <ErrorBoundary componentName="ChatWindow">
            <ChatWindow />
          </ErrorBoundary>
        </div>

        {/* Settings Panel - rendered at app level */}
        <ErrorBoundary componentName="SettingsPanel">
          <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
        </ErrorBoundary>

        {/* System Health Indicator - Field deployment monitoring */}
        {/* Temporarily disabled due to import issues */}
        {/* <ErrorBoundary componentName="SystemHealthIndicator">
          <SystemHealthIndicator
            position="bottom-right"
            enableResourceMonitoring={true}
            enableAutoRecovery={true}
          />
        </ErrorBoundary> */}
      </div>
    </ErrorBoundary>
  );
}

export default App;
