import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from '../store';
import {
  setFormField,
  resetForm,
  submitInteraction,
  addMaterialShared,
  removeMaterialShared,
  addSampleDistributed,
  removeSampleDistributed,
  fetchHCPs,
  fetchMaterials,
  fetchSamples,
  fetchInteractions,
  clearSaveSuccess
} from '../slices/interactionSlice';
import { addUserMessage, sendMessageToAgent } from '../slices/chatSlice';
import { Search, Plus, X, Calendar, Clock, Users, BookOpen, Gift, Award } from 'lucide-react';

export const InteractionForm: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { formData, hcps, materials, samples, isSaving, saveSuccess, error } = useSelector(
    (state: RootState) => state.interaction
  );
  const chatMessages = useSelector((state: RootState) => state.chat.messages);
  const threadId = useSelector((state: RootState) => state.chat.threadId);

  const [hcpSearch, setHcpSearch] = useState('');
  const [showHcpDropdown, setShowHcpDropdown] = useState(false);
  const [showMaterialModal, setShowMaterialModal] = useState(false);
  const [showSampleModal, setShowSampleModal] = useState(false);
  const [materialSearch, setMaterialSearch] = useState('');
  const [sampleSearch, setSampleSearch] = useState('');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    dispatch(fetchHCPs());
    dispatch(fetchMaterials());
    dispatch(fetchSamples());
  }, [dispatch]);

  useEffect(() => {
    if (formData.hcp_name) {
      setHcpSearch(formData.hcp_name);
    } else {
      setHcpSearch('');
    }
  }, [formData.hcp_name]);

  useEffect(() => {
    if (saveSuccess) {
      setToastMessage('🎉 Interaction logged successfully in Database!');
      const timer = setTimeout(() => {
        setToastMessage(null);
        dispatch(clearSaveSuccess());
        dispatch(resetForm());
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [saveSuccess, dispatch]);

  const handleInputChange = (field: any, value: any) => {
    dispatch(setFormField({ field, value }));
  };

  const handleHcpSelect = (hcp: any) => {
    dispatch(setFormField({ field: 'hcp_id', value: hcp.id }));
    dispatch(setFormField({ field: 'hcp_name', value: hcp.name }));
    setHcpSearch(hcp.name);
    setShowHcpDropdown(false);
  };

  const isNewHcp = formData.hcp_name.trim() !== '' && formData.hcp_id === null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.hcp_name) {
      alert('Please select or enter an HCP Name.');
      return;
    }
    if (isNewHcp && formData.hcp_email?.trim()) {
      if (!formData.hcp_email.includes('@')) {
        alert('Please enter a valid Email address for the new HCP.');
        return;
      }
    }
    dispatch(submitInteraction(formData)).then(() => {
      dispatch(fetchInteractions());
      dispatch(fetchHCPs());
    });
  };

  const filteredHcps = hcps.filter((h) =>
    h.name.toLowerCase().includes(hcpSearch.toLowerCase())
  );

  const filteredMaterials = materials.filter((m) =>
    m.name.toLowerCase().includes(materialSearch.toLowerCase())
  );

  const filteredSamples = samples.filter((s) =>
    s.name.toLowerCase().includes(sampleSearch.toLowerCase())
  );

  return (
    <div className="form-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 700 }}>Log HCP Interaction</h2>
        <span className="badge-tag">Draft Mode</span>
      </div>

      {toastMessage && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.15)',
          border: '1px solid var(--success)',
          padding: '12px 16px',
          borderRadius: '8px',
          color: '#34d399',
          marginBottom: '20px',
          fontSize: '0.9rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>{toastMessage}</span>
          <button onClick={() => setToastMessage(null)} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}><X size={16} /></button>
        </div>
      )}

      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid var(--danger)',
          padding: '12px 16px',
          borderRadius: '8px',
          color: '#f87171',
          marginBottom: '20px',
          fontSize: '0.9rem'
        }}>
          Error: {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Section 1: Interaction Details */}
        <h3 className="form-section-title"><Users size={14} /> Interaction Details</h3>
        
        <div className="form-grid">
          <div className="form-group" style={{ position: 'relative' }}>
            <label className="form-label">HCP Name *</label>
            <input
              type="text"
              className="form-input"
              placeholder="Search or select HCP..."
              value={hcpSearch}
              onChange={(e) => {
                setHcpSearch(e.target.value);
                handleInputChange('hcp_name', e.target.value);
                setShowHcpDropdown(true);
              }}
              onFocus={() => setShowHcpDropdown(true)}
            />
            {showHcpDropdown && hcpSearch.length >= 0 && (
              <div className="autocomplete-dropdown">
                {filteredHcps.length > 0 ? (
                  filteredHcps.map((hcp) => (
                    <div
                      key={hcp.id}
                      className="autocomplete-item"
                      onClick={() => handleHcpSelect(hcp)}
                    >
                      <div style={{ fontWeight: 600 }}>{hcp.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {hcp.specialty} • {hcp.clinic}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="autocomplete-item" style={{ color: 'var(--text-muted)', cursor: 'default' }}>
                    No HCP found (Enter to add custom name)
                  </div>
                )}
                <div 
                  className="autocomplete-item" 
                  style={{ borderTop: '1px solid var(--border-color)', color: 'var(--primary)', textAlign: 'center', fontWeight: 500 }}
                  onClick={() => setShowHcpDropdown(false)}
                >
                  Close Dropdown
                </div>
              </div>
            )}
          </div>

          {isNewHcp && (
            <div className="form-field-full" style={{
              background: 'var(--bg-app)',
              border: '1px dashed var(--primary)',
              borderRadius: '12px',
              padding: '20px',
              marginTop: '10px',
              marginBottom: '10px'
            }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '12px' }}>
                👤 New HCP Profile Details (Optional)
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Specialty</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Cardiology, Oncology"
                    value={formData.hcp_specialty || ''}
                    onChange={(e) => handleInputChange('hcp_specialty', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Clinic</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Metro General Hospital"
                    value={formData.hcp_clinic || ''}
                    onChange={(e) => handleInputChange('hcp_clinic', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Email</label>
                  <input
                    type="email"
                    className="form-input"
                    placeholder="doctor@example.com"
                    value={formData.hcp_email || ''}
                    onChange={(e) => handleInputChange('hcp_email', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Clinical Preferences</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Prefers email follow-ups"
                    value={formData.hcp_preferences || ''}
                    onChange={(e) => handleInputChange('hcp_preferences', e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Interaction Type</label>
            <select
              className="form-select"
              value={formData.interaction_type}
              onChange={(e) => handleInputChange('interaction_type', e.target.value)}
            >
              <option value="Meeting">Meeting</option>
              <option value="Call">Call</option>
              <option value="Email">Email</option>
              <option value="Webcast">Webcast</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label"><Calendar size={12} style={{ marginRight: 4 }} /> Date</label>
            <input
              type="date"
              className="form-input"
              value={formData.date}
              onChange={(e) => handleInputChange('date', e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label"><Clock size={12} style={{ marginRight: 4 }} /> Time</label>
            <input
              type="time"
              className="form-input"
              value={formData.time}
              onChange={(e) => handleInputChange('time', e.target.value)}
            />
          </div>

          <div className="form-group form-field-full">
            <label className="form-label">Attendees</label>
            <input
              type="text"
              className="form-input"
              placeholder="Enter names separated by commas..."
              value={formData.attendees}
              onChange={(e) => handleInputChange('attendees', e.target.value)}
            />
          </div>
        </div>

        {/* Section 2: Discussion Content */}
        <h3 className="form-section-title"><BookOpen size={14} /> Topics & Discussion</h3>
        <div className="form-grid">
          <div className="form-group form-field-full">
            <label className="form-label">Topics Discussed</label>
            <textarea
              className="form-textarea"
              placeholder="Enter key discussion points..."
              value={formData.topics_discussed}
              onChange={(e) => handleInputChange('topics_discussed', e.target.value)}
            />
          </div>
        </div>

        {/* Section 3: Materials & Samples */}
        <h3 className="form-section-title"><Gift size={14} /> Materials Shared & Samples Distributed</h3>
        <div className="form-grid">
          <div className="form-group form-field-full">
            <label className="form-label">Materials Shared</label>
            <div className="tag-container">
              {formData.materials_shared.map((mat) => (
                <div key={mat} className="tag-item">
                  <span>{mat}</span>
                  <button
                    type="button"
                    className="tag-remove-btn"
                    onClick={() => dispatch(removeMaterialShared(mat))}
                  >
                    <X size={12} />
                  </button>
                </div>
              ))}
              {formData.materials_shared.length === 0 && (
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>No materials added.</span>
              )}
            </div>
            <button
              type="button"
              className="btn-secondary"
              style={{ alignSelf: 'flex-start', marginTop: '6px' }}
              onClick={() => setShowMaterialModal(true)}
            >
              <Search size={14} /> Search/Add Materials
            </button>
          </div>

          <div className="form-group form-field-full">
            <label className="form-label">Samples Distributed</label>
            <div className="tag-container">
              {formData.samples_distributed.map((sam) => (
                <div key={sam} className="tag-item">
                  <span>{sam}</span>
                  <button
                    type="button"
                    className="tag-remove-btn"
                    onClick={() => dispatch(removeSampleDistributed(sam))}
                  >
                    <X size={12} />
                  </button>
                </div>
              ))}
              {formData.samples_distributed.length === 0 && (
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>No samples added.</span>
              )}
            </div>
            <button
              type="button"
              className="btn-secondary"
              style={{ alignSelf: 'flex-start', marginTop: '6px' }}
              onClick={() => setShowSampleModal(true)}
            >
              <Plus size={14} /> Add Sample
            </button>
          </div>
        </div>

        {/* Section 4: Sentiment & Outcomes */}
        <h3 className="form-section-title"><Award size={14} /> Sentiment, Outcomes & Next Steps</h3>
        <div className="form-grid">
          <div className="form-group form-field-full">
            <label className="form-label">Observed/Inferred HCP Sentiment</label>
            <div className="sentiment-container">
              <div
                className={`sentiment-option ${formData.sentiment === 'Positive' ? 'active positive' : ''}`}
                onClick={() => handleInputChange('sentiment', 'Positive')}
              >
                😊 Positive
              </div>
              <div
                className={`sentiment-option ${formData.sentiment === 'Neutral' ? 'active neutral' : ''}`}
                onClick={() => handleInputChange('sentiment', 'Neutral')}
              >
                😐 Neutral
              </div>
              <div
                className={`sentiment-option ${formData.sentiment === 'Negative' ? 'active negative' : ''}`}
                onClick={() => handleInputChange('sentiment', 'Negative')}
              >
                😡 Negative
              </div>
            </div>
          </div>

          <div className="form-group form-field-full">
            <label className="form-label">Outcomes</label>
            <textarea
              className="form-textarea"
              placeholder="Key outcomes or agreements..."
              value={formData.outcomes}
              onChange={(e) => handleInputChange('outcomes', e.target.value)}
            />
          </div>

          <div className="form-group form-field-full">
            <label className="form-label">Follow-up Actions</label>
            <textarea
              className="form-textarea"
              placeholder="Enter follow-up steps..."
              value={formData.follow_up_actions}
              onChange={(e) => handleInputChange('follow_up_actions', e.target.value)}
            />
          </div>
        </div>

        <div className="action-row" style={{ marginTop: '30px', borderTop: '1px solid var(--border-color)', paddingTop: '20px' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => {
              dispatch(resetForm());
              setHcpSearch('');
            }}
          >
            Reset
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={isSaving}
          >
            {isSaving ? 'Logging Interaction...' : 'Submit Interaction'}
          </button>
        </div>
      </form>

      {/* --- Material Selection Modal --- */}
      {showMaterialModal && (
        <div className="modal-overlay" onClick={() => setShowMaterialModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h4 className="modal-title">Select Materials Shared</h4>
              <button className="modal-close-btn" onClick={() => setShowMaterialModal(false)}>
                <X size={18} />
              </button>
            </div>
            <div className="modal-body">
              <div className="modal-search-box">
                <Search size={16} style={{ color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  className="modal-search-input"
                  placeholder="Search materials..."
                  value={materialSearch}
                  onChange={(e) => setMaterialSearch(e.target.value)}
                />
              </div>
              <div className="modal-list">
                {filteredMaterials.map((mat) => {
                  const isSelected = formData.materials_shared.includes(mat.name);
                  return (
                    <div
                      key={mat.id}
                      className="modal-list-item"
                      style={{ borderColor: isSelected ? 'var(--primary)' : 'var(--border-color)' }}
                      onClick={() => {
                        if (isSelected) {
                          dispatch(removeMaterialShared(mat.name));
                        } else {
                          dispatch(addMaterialShared(mat.name));
                        }
                      }}
                    >
                      <div>
                        <div className="modal-item-name">{mat.name}</div>
                        <div className="modal-item-desc">{mat.type} • {mat.file_size}</div>
                      </div>
                      <span style={{ fontSize: '0.8rem', color: isSelected ? 'var(--primary)' : 'var(--text-muted)' }}>
                        {isSelected ? 'Added ✓' : '+ Add'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --- Sample Selection Modal --- */}
      {showSampleModal && (
        <div className="modal-overlay" onClick={() => setShowSampleModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h4 className="modal-title">Select Samples Distributed</h4>
              <button className="modal-close-btn" onClick={() => setShowSampleModal(false)}>
                <X size={18} />
              </button>
            </div>
            <div className="modal-body">
              <div className="modal-search-box">
                <Search size={16} style={{ color: 'var(--text-muted)' }} />
                <input
                  type="text"
                  className="modal-search-input"
                  placeholder="Search samples..."
                  value={sampleSearch}
                  onChange={(e) => setSampleSearch(e.target.value)}
                />
              </div>
              <div className="modal-list">
                {filteredSamples.map((sam) => {
                  const isSelected = formData.samples_distributed.includes(sam.name);
                  return (
                    <div
                      key={sam.id}
                      className="modal-list-item"
                      style={{ borderColor: isSelected ? 'var(--primary)' : 'var(--border-color)' }}
                      onClick={() => {
                        if (isSelected) {
                          dispatch(removeSampleDistributed(sam.name));
                        } else {
                          dispatch(addSampleDistributed(sam.name));
                        }
                      }}
                    >
                      <div>
                        <div className="modal-item-name">{sam.name}</div>
                        <div className="modal-item-desc">{sam.description}</div>
                      </div>
                      <span style={{ fontSize: '0.8rem', color: isSelected ? 'var(--primary)' : 'var(--text-muted)' }}>
                        {isSelected ? 'Added ✓' : '+ Add'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
