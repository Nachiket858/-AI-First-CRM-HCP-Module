import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from '../store';
import { fetchInteractions } from '../slices/interactionSlice';
import { Calendar, Clock, MessageSquare, Award, AlertCircle, ArrowRight } from 'lucide-react';

export const InteractionHistory: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { interactions, loading, error } = useSelector((state: RootState) => state.interaction);

  useEffect(() => {
    dispatch(fetchInteractions());
  }, [dispatch]);

  const getSentimentEmoji = (sentiment: string) => {
    switch (sentiment) {
      case 'Positive': return '😊';
      case 'Neutral': return '😐';
      case 'Negative': return '😡';
      default: return '💬';
    }
  };

  const getSentimentClass = (sentiment: string) => {
    switch (sentiment) {
      case 'Positive': return 'active positive';
      case 'Neutral': return 'active neutral';
      case 'Negative': return 'active negative';
      default: return '';
    }
  };

  return (
    <div className="history-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700 }}>Interaction Logs</h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Database records of all recent representative actions
          </p>
        </div>
        <span className="badge-tag">{interactions.length} Logs</span>
      </div>

      {loading && interactions.length === 0 && <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>Loading history...</div>}

      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fee2e2', padding: '16px', borderRadius: '8px', color: 'var(--danger)', marginBottom: '20px', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <AlertCircle size={16} /> Error loading interaction history: {error}
        </div>
      )}

      {!loading && !error && interactions.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)', background: '#ffffff', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
          No logged interactions found. Fill out the form or use the AI Assistant to log a new interaction.
        </div>
      )}

      <div className="history-timeline">
        {interactions.map((log) => (
          <div key={log.id} className="history-card">
            {/* Header */}
            <div className="history-card-header">
              <div>
                <h4 className="history-hcp-name">{log.hcp_name}</h4>
                <div style={{ display: 'flex', gap: '12px', marginTop: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Calendar size={12} /> {log.date}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} /> {log.time}
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span className="badge-tag" style={{ background: '#ffffff', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}>
                  {log.interaction_type}
                </span>
                <span className={`sentiment-badge ${getSentimentClass(log.sentiment)}`}>
                  {getSentimentEmoji(log.sentiment)} {log.sentiment}
                </span>
              </div>
            </div>

            {/* Body */}
            <div className="history-card-body">
              {log.topics_discussed && (
                <div className="history-section">
                  <div className="history-section-title">
                    <MessageSquare size={12} /> Topics Discussed
                  </div>
                  <div className="history-section-text">{log.topics_discussed}</div>
                </div>
              )}

              {log.outcomes && (
                <div className="history-section">
                  <div className="history-section-title">
                    <Award size={12} /> Outcomes
                  </div>
                  <div className="history-section-text">{log.outcomes}</div>
                </div>
              )}

              {log.follow_up_actions && (
                <div className="history-section">
                  <div className="history-section-title">
                    <ArrowRight size={12} /> Follow-up Actions
                  </div>
                  <div className="history-section-text" style={{ whiteSpace: 'pre-line' }}>{log.follow_up_actions}</div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
