import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import type { RootState } from '../store';
import { Search, Mail, Phone, MapPin, Heart, ShieldAlert } from 'lucide-react';

export const HcpDirectory: React.FC = () => {
  const { hcps, loading, error } = useSelector((state: RootState) => state.interaction);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredHcps = hcps.filter(
    (hcp) =>
      hcp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      hcp.specialty.toLowerCase().includes(searchQuery.toLowerCase()) ||
      hcp.clinic.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="directory-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700 }}>HCP Directory</h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            List of registered healthcare professionals in database
          </p>
        </div>
        <span className="badge-tag">{hcps.length} Doctors</span>
      </div>

      {/* Search Box */}
      <div className="modal-search-box" style={{ marginBottom: '24px', background: '#ffffff', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
        <Search size={16} style={{ color: 'var(--text-muted)' }} />
        <input
          type="text"
          className="modal-search-input"
          placeholder="Search by doctor name, specialty, or clinic..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {loading && <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>Loading directory...</div>}
      
      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fee2e2', padding: '16px', borderRadius: '8px', color: 'var(--danger)', marginBottom: '20px', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <ShieldAlert size={16} /> Error loading directory: {error}
        </div>
      )}

      {!loading && !error && filteredHcps.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)', background: '#ffffff', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
          No healthcare professionals found matching "{searchQuery}"
        </div>
      )}

      <div className="directory-list">
        {filteredHcps.map((hcp) => (
          <div key={hcp.id} className="directory-card">
            <div className="directory-card-header">
              <div>
                <h4 className="directory-name">{hcp.name}</h4>
                <span className="directory-specialty">{hcp.specialty}</span>
              </div>
            </div>

            <div className="directory-card-body">
              <div className="directory-info-row">
                <MapPin size={14} className="directory-info-icon" />
                <span>{hcp.clinic}</span>
              </div>
              <div className="directory-info-row">
                <Mail size={14} className="directory-info-icon" />
                <a href={`mailto:${hcp.email}`} className="directory-link">{hcp.email}</a>
              </div>
              {hcp.preferences && (
                <div className="directory-preferences">
                  <div className="directory-pref-title">
                    <Heart size={12} style={{ color: 'var(--primary)' }} /> Clinical Preferences
                  </div>
                  <div className="directory-pref-text">{hcp.preferences}</div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
