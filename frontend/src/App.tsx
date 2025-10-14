import { useEffect } from 'react';
import { ChatWindow } from './components/Chat/ChatWindow';
import { Sidebar } from './components/Layout/Sidebar';
import { Header } from './components/Layout/Header';
import useStore from './store/useStore';

function App() {
  const darkMode = useStore((state) => state.settings.darkMode);

  // Apply dark mode class to document on mount and when darkMode changes
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />

        {/* Chat window */}
        <ChatWindow />
      </div>
    </div>
  );
}

export default App;
