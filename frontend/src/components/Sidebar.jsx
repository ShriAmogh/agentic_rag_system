import React, { useState } from 'react';
import { BookOpen, FilePlus, Search, CheckCircle, Clock, RotateCw } from 'lucide-react';

export default function Sidebar({ papers, selectedPaperId, onSelectPaper, onOpenUploadModal, onRefreshPapers }) {
  const [filterText, setFilterText] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    if (onRefreshPapers) await onRefreshPapers();
    setTimeout(() => setRefreshing(false), 500);
  };

  const filteredPapers = papers.filter((p) =>
    p.title.toLowerCase().includes(filterText.toLowerCase()) ||
    (p.paper_id && p.paper_id.toLowerCase().includes(filterText.toLowerCase()))
  );

  return (
    <aside style={{
      width: '320px',
      height: '100%',
      backgroundColor: 'var(--bg-panel)',
      borderRight: '1px solid var(--border-glass)',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0
    }}>
      {/* Sidebar Header */}
      <div style={{ padding: '20px', borderBottom: '1px solid var(--border-glass)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BookOpen size={20} color="var(--primary-cyan)" />
            <h2 style={{ fontSize: '1.1rem', fontWeight: '700' }}>Papers</h2>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={handleRefresh}
              title="Refresh Papers List"
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                padding: '4px'
              }}
            >
              <RotateCw size={14} className={refreshing ? 'animate-spin' : ''} />
            </button>
            <span style={{
              fontSize: '0.75rem',
              background: 'rgba(6, 182, 212, 0.15)',
              color: 'var(--primary-cyan)',
              padding: '2px 8px',
              borderRadius: '12px',
              fontWeight: '600'
            }}>
              {papers.length}
            </span>
          </div>
        </div>

        {/* Upload Button */}
        <button
          onClick={onOpenUploadModal}
          className="glow-btn"
          style={{ width: '100%', justifyContent: 'center', marginBottom: '12px', fontSize: '0.85rem' }}
        >
          <FilePlus size={16} />
          Upload New PDF Paper
        </button>

        {/* Search input for sidebar */}
        <div style={{ position: 'relative' }}>
          <Search size={14} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-dim)' }} />
          <input
            type="text"
            placeholder="Filter paper topics..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px 8px 30px',
              backgroundColor: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid var(--border-glass)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-main)',
              fontSize: '0.8rem',
              outline: 'none'
            }}
          />
        </div>
      </div>

      {/* Papers List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
        {papers.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            <p style={{ marginBottom: '10px' }}>Loading papers...</p>
            <button
              onClick={handleRefresh}
              style={{
                padding: '6px 12px',
                background: 'var(--primary-indigo)',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.75rem',
                fontWeight: '600'
              }}
            >
              Retry Loading Papers
            </button>
          </div>
        ) : filteredPapers.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No papers match your filter "{filterText}".
          </div>
        ) : (
          filteredPapers.map((paper) => {
            const isSelected = selectedPaperId === paper.paper_id;
            return (
              <div
                key={paper.paper_id}
                onClick={() => onSelectPaper(paper)}
                style={{
                  padding: '12px',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '8px',
                  cursor: 'pointer',
                  backgroundColor: isSelected ? 'rgba(99, 102, 241, 0.2)' : 'rgba(30, 41, 59, 0.4)',
                  border: isSelected ? '1px solid var(--primary-indigo)' : '1px solid transparent',
                  transition: 'var(--transition-smooth)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
                  <h4 style={{
                    fontSize: '0.85rem',
                    fontWeight: '600',
                    color: isSelected ? 'var(--text-main)' : 'var(--text-muted)',
                    lineHeight: '1.3',
                    marginBottom: '6px'
                  }}>
                    {paper.title}
                  </h4>
                  {isSelected && <CheckCircle size={14} color="var(--primary-cyan)" style={{ flexShrink: 0 }} />}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} /> {paper.submission_date || 'N/A'}
                  </span>
                  <span>ID: {paper.paper_id}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
