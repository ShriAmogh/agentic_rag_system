import React from 'react';
import { Columns, CheckCircle2, AlertTriangle, ShieldCheck, Zap, Layers } from 'lucide-react';

export default function ComparativeMatrix({ data, auditReport, onClose }) {
  if (!data) return null;

  const { comparison_topic, summary_matrix, synthesis_takeaway } = data;

  return (
    <div className="glass-card" style={{ padding: '24px', marginTop: '24px', animation: 'fadeIn 0.3s ease-in-out' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'rgba(99, 102, 241, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Columns size={22} color="var(--primary-indigo)" />
          </div>
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: '700' }}>Literature Review & Comparative Analysis</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Topic: {comparison_topic || 'Multi-Paper Benchmark'}</p>
          </div>
        </div>

        {/* Audit Report Badge */}
        {auditReport && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 14px',
            borderRadius: '20px',
            backgroundColor: auditReport.audit_passed ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
            border: auditReport.audit_passed ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(245, 158, 11, 0.4)',
            color: auditReport.audit_passed ? '#10b981' : '#f59e0b',
            fontSize: '0.78rem',
            fontWeight: '600'
          }}>
            <ShieldCheck size={16} />
            <span>Audit: {auditReport.audit_passed ? 'Factual Grounding Passed' : 'Fact Check Review Needed'}</span>
            <span style={{ opacity: 0.8, fontSize: '0.7rem' }}>({auditReport.hallucination_score?.toFixed(1) || 0}% ungrounded)</span>
          </div>
        )}
      </div>

      {/* Synthesis Takeaway Card */}
      {synthesis_takeaway && (
        <div style={{
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          borderLeft: '4px solid var(--primary-cyan)',
          padding: '16px 20px',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '24px'
        }}>
          <h4 style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--primary-cyan)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Synthesis & Tradeoff Takeaway
          </h4>
          <p style={{ fontSize: '0.9rem', lineHeight: '1.5', color: 'var(--text-main)' }}>
            {synthesis_takeaway}
          </p>
        </div>
      )}

      {/* Comparative Grid Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {summary_matrix && summary_matrix.map((item, idx) => (
          <div key={idx} style={{
            backgroundColor: 'rgba(30, 41, 59, 0.5)',
            border: '1px solid var(--border-glass)',
            borderRadius: 'var(--radius-md)',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            justify: 'space-between'
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--primary-cyan)', fontWeight: '700', textTransform: 'uppercase' }}>
                  ID: {item.paper_id}
                </span>
                <span style={{
                  fontSize: '0.7rem',
                  padding: '2px 8px',
                  borderRadius: '10px',
                  backgroundColor: item.compute_overhead === 'High' ? 'rgba(239, 68, 68, 0.2)' : item.compute_overhead === 'Medium' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                  color: item.compute_overhead === 'High' ? '#ef4444' : item.compute_overhead === 'Medium' ? '#f59e0b' : '#10b981',
                  fontWeight: '600'
                }}>
                  Compute: {item.compute_overhead}
                </span>
              </div>

              <h4 style={{ fontSize: '0.95rem', fontWeight: '700', marginBottom: '12px', color: 'var(--text-main)' }}>
                {item.title}
              </h4>

              <div style={{ marginBottom: '14px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>
                  KEY METHODOLOGY
                </span>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                  {item.key_methodology}
                </p>
              </div>

              {/* Strengths & Limitations */}
              <div style={{ marginBottom: '12px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                  <CheckCircle2 size={12} /> STRENGTHS
                </span>
                <ul style={{ paddingLeft: '16px', margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {item.strengths && item.strengths.map((str, sIdx) => (
                    <li key={sIdx}>{str}</li>
                  ))}
                </ul>
              </div>

              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                  <AlertTriangle size={12} /> LIMITATIONS
                </span>
                <ul style={{ paddingLeft: '16px', margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {item.limitations && item.limitations.map((lim, lIdx) => (
                    <li key={lIdx}>{lim}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
