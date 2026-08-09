import React, { useState } from 'react';
import { Sparkles, Code, CheckCircle, BarChart3 } from 'lucide-react';

export default function SummaryCard({ summaryData }) {
  const [showRaw, setShowRaw] = useState(false);

  if (!summaryData) return null;

  const score = summaryData.complexity_score || 5;
  const getScoreColor = (val) => {
    if (val <= 3) return '#10b981';
    if (val <= 7) return '#06b6d4';
    return '#8b5cf6';
  };

  return (
    <div className="glass-card" style={{ padding: '24px', marginBottom: '24px', position: 'relative' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={20} color="var(--primary-cyan)" />
          <h3 style={{ fontSize: '1.1rem', fontWeight: '700' }}>Validated Agentic Paper Summary</h3>
        </div>
        <button
          onClick={() => setShowRaw(!showRaw)}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border-glass)',
            color: 'var(--text-muted)',
            padding: '4px 10px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.75rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <Code size={14} /> {showRaw ? 'Hide JSON' : 'View Raw JSON'}
        </button>
      </div>

      {showRaw ? (
        <pre style={{
          backgroundColor: '#030712',
          padding: '16px',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.8rem',
          color: '#38bdf8',
          overflowX: 'auto',
          border: '1px solid var(--border-glass)'
        }}>
          {JSON.stringify(summaryData, null, 2)}
        </pre>
      ) : (
        <div>
          {/* Complexity score meter */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            padding: '12px 16px',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '16px',
            border: '1px solid var(--border-glass)'
          }}>
            <BarChart3 size={18} color={getScoreColor(score)} />
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Technical Complexity Rating:</span>
                <span style={{ fontWeight: '700', color: getScoreColor(score) }}>{score} / 10</span>
              </div>
              <div style={{ height: '6px', width: '100%', backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${(score / 10) * 100}%`,
                  backgroundColor: getScoreColor(score),
                  transition: 'width 0.5s ease-in-out'
                }} />
              </div>
            </div>
          </div>

          {/* Abstract Summary */}
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ fontSize: '0.85rem', color: 'var(--primary-cyan)', marginBottom: '6px', fontWeight: '600' }}>
              Executive Summary
            </h4>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', lineHeight: '1.6' }}>
              {summaryData.summary}
            </p>
          </div>

          {/* Future Work */}
          {summaryData.future_work && (
            <div>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--primary-violet)', marginBottom: '6px', fontWeight: '600' }}>
                Future Work & Opportunities
              </h4>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                {summaryData.future_work}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
