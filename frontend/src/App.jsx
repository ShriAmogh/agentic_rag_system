import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import PdfUploadModal from './components/PdfUploadModal';
import SummaryCard from './components/SummaryCard';
import ChatWindow from './components/ChatWindow';
import ComparativeMatrix from './components/ComparativeMatrix';
import { Search, Sparkles, BookOpen, MessageSquare, Loader2, Cpu, CheckCircle, Columns } from 'lucide-react';

export default function App() {
  const [papers, setPapers] = useState([]);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [discoveredPapers, setDiscoveredPapers] = useState([]);

  const [comparativeData, setComparativeData] = useState(null);
  const [comparativeAudit, setComparativeAudit] = useState(null);
  const [isComparing, setIsComparing] = useState(false);

  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const [searchError, setSearchError] = useState(null);

  // Load all ingested papers on mount with auto-retry
  const fetchPapers = async () => {
    try {
      const res = await fetch('/api/papers');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setPapers(data);
          return data;
        }
      }
    } catch (err) {
      console.error('Failed to fetch papers:', err);
    }
    return null;
  };

  useEffect(() => {
    fetchPapers();
    const timer = setInterval(async () => {
      const data = await fetchPapers();
      if (data && data.length > 0) {
        clearInterval(timer);
      }
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  // Handle Search Submission
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    if (papers.length === 0) {
      fetchPapers();
    }

    setIsSearching(true);
    setSearchError(null);
    setDiscoveredPapers([]);
    setSummaryData(null);
    setComparativeData(null);
    setComparativeAudit(null);

    try {
      const res = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery.trim()
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Search failed.');
      }

      setDiscoveredPapers(data.discovered_papers || []);

      if (data.discovered_papers && data.discovered_papers.length > 0) {
        const firstPaper = data.discovered_papers[0];
        handleSelectAndSummarize(firstPaper, searchQuery.trim());
      }
    } catch (err) {
      setSearchError(err.message);
    } finally {
      setIsSearching(false);
    }
  };

  // Run Literature Review & Comparative Analysis across top papers
  const handleCompare = async () => {
    setIsComparing(true);
    setComparativeData(null);
    setComparativeAudit(null);

    try {
      const paperIds = discoveredPapers.slice(0, 4).map((p) => p.paper_id);
      const res = await fetch('/api/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery.trim() || 'comparative analysis',
          paper_ids: paperIds
        })
      });

      const data = await res.json();
      if (res.ok && data.comparative_analysis) {
        setComparativeData(data.comparative_analysis);
        setComparativeAudit(data.audit_report);
      }
    } catch (err) {
      console.error('Failed to run comparative analysis:', err);
    } finally {
      setIsComparing(false);
    }
  };

  // Select a paper and generate its Pydantic JSON summary
  const handleSelectAndSummarize = async (paperObj, currentQuery = searchQuery) => {
    setSelectedPaper(paperObj);
    setIsSummarizing(true);
    setSummaryData(null);

    try {
      const res = await fetch('/api/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: currentQuery.trim() || 'overview',
          paper_id: paperObj.paper_id
        })
      });

      const data = await res.json();
      if (res.ok && data.summary) {
        setSummaryData(data.summary);
      }
    } catch (err) {
      console.error('Failed to summarize paper:', err);
    } finally {
      setIsSummarizing(false);
    }
  };

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', backgroundColor: 'var(--bg-dark)' }}>
      {/* Sidebar Component */}
      <Sidebar
        papers={papers}
        selectedPaperId={selectedPaper?.paper_id}
        onSelectPaper={(p) => handleSelectAndSummarize(p)}
        onOpenUploadModal={() => setIsUploadOpen(true)}
        onRefreshPapers={fetchPapers}
      />

      {/* Main Workspace Area */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto' }}>
        {/* Top Header */}
        <header style={{
          padding: '16px 32px',
          borderBottom: '1px solid var(--border-glass)',
          backgroundColor: 'rgba(15, 23, 42, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backdropFilter: 'blur(12px)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Cpu size={26} color="var(--primary-cyan)" className="pulse" />
            <div>
              <h1 style={{ fontSize: '1.25rem', fontWeight: '700', letterSpacing: '-0.5px' }}>
                Research Explorer
              </h1>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                Academic Paper Discovery & Literature Review
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          </div>
        </header>

        {/* Workspace Body */}
        <div style={{ padding: '32px', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
          {/* Hero Search Box */}
          <div className="glass-card" style={{ padding: '24px', marginBottom: '32px' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Search size={18} color="var(--primary-cyan)" /> Search & Discover Papers
            </h2>

            <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: '280px', position: 'relative' }}>
                <input
                  type="text"
                  placeholder="e.g. LLM as judge paper published after 2025..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    backgroundColor: 'rgba(15, 23, 42, 0.8)',
                    border: '1px solid var(--border-glass)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-main)',
                    fontSize: '0.95rem',
                    outline: 'none'
                  }}
                />
              </div>

              <button type="submit" disabled={isSearching} className="glow-btn">
                {isSearching ? (
                  <>
                    <Loader2 size={16} className="animate-spin" /> Searching...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} /> Discover Papers
                  </>
                )}
              </button>
            </form>

            {searchError && (
              <div style={{ color: '#f87171', fontSize: '0.85rem', marginTop: '12px' }}>
                ⚠️ {searchError}
              </div>
            )}
          </div>

          {/* Discovered Papers Cards */}
          {discoveredPapers.length > 0 && (
            <div style={{ marginBottom: '32px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BookOpen size={16} /> Discovered Papers ({discoveredPapers.length})
                </h3>

                {discoveredPapers.length >= 2 && (
                  <button
                    onClick={handleCompare}
                    disabled={isComparing}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 16px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'rgba(99, 102, 241, 0.2)',
                      border: '1px solid var(--primary-indigo)',
                      color: '#a5b4fc',
                      fontSize: '0.82rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    {isComparing ? (
                      <>
                        <Loader2 size={14} className="animate-spin" /> Comparing...
                      </>
                    ) : (
                      <>
                        <Columns size={14} /> Compare Papers
                      </>
                    )}
                  </button>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
                {discoveredPapers.map((paper) => {
                  const isSelected = selectedPaper?.paper_id === paper.paper_id;
                  return (
                    <div
                      key={paper.paper_id}
                      onClick={() => handleSelectAndSummarize(paper)}
                      className="glass-card"
                      style={{
                        padding: '16px',
                        cursor: 'pointer',
                        borderColor: isSelected ? 'var(--primary-cyan)' : 'var(--border-glass)',
                        backgroundColor: isSelected ? 'rgba(6, 182, 212, 0.1)' : 'var(--bg-card)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: '700', lineHeight: '1.3' }}>
                          {paper.title}
                        </h4>
                        {isSelected && <CheckCircle size={16} color="var(--primary-cyan)" style={{ flexShrink: 0 }} />}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        Date: {paper.submission_date} | ID: {paper.paper_id}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Side-by-Side Comparative Matrix */}
              {isComparing ? (
                <div className="glass-card" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)', marginTop: '24px' }}>
                  <Loader2 size={24} className="animate-spin" style={{ margin: '0 auto 12px auto', color: 'var(--primary-indigo)' }} />
                  Generating side-by-side literature review...
                </div>
              ) : (
                comparativeData && <ComparativeMatrix data={comparativeData} auditReport={comparativeAudit} />
              )}
            </div>
          )}

          {/* Selected Paper Details Dashboard */}
          {selectedPaper ? (
            <div>
              {/* Paper Summary Section */}
              {isSummarizing ? (
                <div className="glass-card" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <Loader2 size={24} className="animate-spin" style={{ margin: '0 auto 12px auto', color: 'var(--primary-cyan)' }} />
                  Summarizing "{selectedPaper.title}"...
                </div>
              ) : (
                summaryData && <SummaryCard summaryData={summaryData} />
              )}

              {/* Multi-Turn RAG Chat Window */}
              <ChatWindow
                selectedPaper={selectedPaper}
                onBackToSearch={() => {
                  setSelectedPaper(null);
                  setSummaryData(null);
                }}
              />
            </div>
          ) : (
            !isSearching && (
              <div className="glass-card" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
                <BookOpen size={40} color="var(--primary-indigo)" style={{ margin: '0 auto 16px auto', opacity: 0.8 }} />
                <h3 style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--text-main)', marginBottom: '8px' }}>
                  Select or Discover an Academic Paper
                </h3>
                <p style={{ fontSize: '0.9rem', maxWidth: '500px', margin: '0 auto' }}>
                  Use the search bar above or choose a paper from the left sidebar to view its summary and chat in real-time.
                </p>
              </div>
            )
          )}
        </div>
      </main>

      {/* PDF Upload Modal */}
      <PdfUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={fetchPapers}
      />
    </div>
  );
}
