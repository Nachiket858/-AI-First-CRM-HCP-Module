import { useState } from 'react';
import { InteractionForm } from './components/InteractionForm';
import { HcpDirectory } from './components/HcpDirectory';
import { InteractionHistory } from './components/InteractionHistory';
import { AIAssistant } from './components/AIAssistant';
import { FileText, Users, History } from 'lucide-react';

function App() {
  const [activeView, setActiveView] = useState<'form' | 'directory' | 'history'>('form');

  return (
    <div className="app-container">
      {/* Premium Header */}
      <header className="app-header">
        <div className="logo-section">
          <div className="logo-icon">Ω</div>
          <div className="logo-text">Aegis CRM</div>
          <span className="badge-tag">HCP Interaction Module</span>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Welcome, Sales Rep • <strong>Active Workspace</strong>
        </div>
      </header>

      {/* Main Layout containing Sidebar + Content split */}
      <div className="main-content">
        {/* Navigation Sidebar */}
        <nav className="sidebar-nav">
          <button 
            className={`sidebar-nav-btn ${activeView === 'form' ? 'active' : ''}`}
            onClick={() => setActiveView('form')}
            title="Log Interaction Form"
          >
            <FileText size={20} />
            <span className="sidebar-nav-label">Log Visit</span>
          </button>
          <button 
            className={`sidebar-nav-btn ${activeView === 'directory' ? 'active' : ''}`}
            onClick={() => setActiveView('directory')}
            title="HCP Directory"
          >
            <Users size={20} />
            <span className="sidebar-nav-label">Directory</span>
          </button>
          <button 
            className={`sidebar-nav-btn ${activeView === 'history' ? 'active' : ''}`}
            onClick={() => setActiveView('history')}
            title="Interaction History"
          >
            <History size={20} />
            <span className="sidebar-nav-label">Logs</span>
          </button>
        </nav>

        {/* Dynamic Left Column Panel */}
        <div className="dynamic-panel-container">
          {activeView === 'form' && <InteractionForm />}
          {activeView === 'directory' && <HcpDirectory />}
          {activeView === 'history' && <InteractionHistory />}
        </div>

        {/* Right Column Panel: AI Assistant */}
        <AIAssistant />
      </div>
    </div>
  );
}

export default App;
