import { InteractionForm } from './components/InteractionForm';
import { AIAssistant } from './components/AIAssistant';

function App() {
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

      {/* Main Split Screen */}
      <div className="main-content">
        <InteractionForm />
        <AIAssistant />
      </div>
    </div>
  );
}

export default App;
