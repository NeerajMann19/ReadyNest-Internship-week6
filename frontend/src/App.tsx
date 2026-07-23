import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { SessionProvider } from './context/SessionContext';
import Sidebar from './components/layout/Sidebar';
import TopNav from './components/layout/TopNav';
import Overview from './pages/Overview';
import Analytics from './pages/Analytics';
import Predictions from './pages/Predictions';
import Report from './pages/Report';
import DecisionCenter from './pages/DecisionCenter';

/**
 * Main Application Component
 * Configures SessionProvider, BrowserRouter, Layout Shell (Sidebar + TopNav), and Page Routes.
 */
export const App: React.FC = () => {
  return (
    <SessionProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-background text-text-primary flex">
          {/* Fixed Desktop Sidebar */}
          <Sidebar />

          {/* Main Content Area Shell */}
          <div className="flex-1 flex flex-col md:ml-64 min-h-screen bg-background">
            <TopNav />
            <main className="p-8 flex-1 overflow-y-auto">
              <Routes>
                <Route path="/" element={<Overview />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/predictions" element={<Predictions />} />
                <Route path="/report" element={<Report />} />
                <Route path="/decision" element={<DecisionCenter />} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </SessionProvider>
  );
};

export default App;
