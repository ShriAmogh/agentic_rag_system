import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Bot, User, Loader2, ArrowLeft } from 'lucide-react';

export default function ChatWindow({ selectedPaper, onBackToSearch }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Reset messages when active paper changes
  useEffect(() => {
    setMessages([
      {
        role: 'assistant',
        content: `Hello! I am ready to answer any questions about the paper **"${selectedPaper.title}"**. What would you like to know?`
      }
    ]);
  }, [selectedPaper.paper_id]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userText = inputValue.trim();
    setInputValue('');

    const newHistory = [...messages, { role: 'user', content: userText }];
    setMessages(newHistory);
    setLoading(true);

    try {
      // Build history payload (excluding initial system greeting if any)
      const historyPayload = newHistory
        .filter((m, idx) => idx > 0)
        .map((m) => ({ role: m.role, content: m.content }));

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userText,
          paper_id: selectedPaper.paper_id,
          history: historyPayload
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Chat request failed.');
      }

      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `⚠️ Error: ${err.message}` }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card" style={{
      display: 'flex',
      flexDirection: 'column',
      height: '540px',
      overflow: 'hidden',
      position: 'relative'
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border-glass)',
        backgroundColor: 'rgba(15, 23, 42, 0.7)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <MessageSquare size={20} color="var(--primary-indigo)" />
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--primary-cyan)', fontWeight: '600' }}>
              Multi-Turn RAG Conversational Mode
            </div>
            <div style={{ fontSize: '0.9rem', fontWeight: '700', color: 'var(--text-main)' }}>
              {selectedPaper.title}
            </div>
          </div>
        </div>

        <button
          onClick={onBackToSearch}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border-glass)',
            color: 'var(--text-muted)',
            padding: '6px 12px',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.8rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <ArrowLeft size={14} /> Back to Search
        </button>
      </div>

      {/* Messages List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={index}
              style={{
                display: 'flex',
                gap: '12px',
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                maxWidth: '85%'
              }}
            >
              {!isUser && (
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(99, 102, 241, 0.2)',
                  border: '1px solid var(--primary-indigo)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  <Bot size={18} color="var(--primary-indigo)" />
                </div>
              )}

              <div style={{
                padding: '12px 16px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: isUser ? 'var(--primary-indigo)' : 'rgba(30, 41, 59, 0.8)',
                color: isUser ? '#ffffff' : 'var(--text-main)',
                fontSize: '0.9rem',
                lineHeight: '1.5',
                border: isUser ? 'none' : '1px solid var(--border-glass)'
              }}>
                {msg.content}
              </div>

              {isUser && (
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(6, 182, 212, 0.2)',
                  border: '1px solid var(--primary-cyan)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  <User size={18} color="var(--primary-cyan)" />
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div style={{ display: 'flex', gap: '12px', alignSelf: 'flex-start' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: 'rgba(99, 102, 241, 0.2)',
              border: '1px solid var(--primary-indigo)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Bot size={18} color="var(--primary-indigo)" />
            </div>
            <div style={{
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              border: '1px solid var(--border-glass)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: 'var(--text-muted)',
              fontSize: '0.85rem'
            }}>
              <Loader2 size={16} className="animate-spin" /> Retrieving context & reasoning...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <form onSubmit={handleSend} style={{
        padding: '16px',
        borderTop: '1px solid var(--border-glass)',
        backgroundColor: 'rgba(15, 23, 42, 0.8)',
        display: 'flex',
        gap: '10px'
      }}>
        <input
          type="text"
          placeholder={`Ask a question about ${selectedPaper.title}...`}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          disabled={loading}
          style={{
            flex: 1,
            padding: '12px 16px',
            backgroundColor: 'rgba(30, 41, 59, 0.6)',
            border: '1px solid var(--border-glass)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-main)',
            fontSize: '0.9rem',
            outline: 'none'
          }}
        />
        <button type="submit" disabled={loading || !inputValue.trim()} className="glow-btn">
          <Send size={16} /> Send
        </button>
      </form>
    </div>
  );
}
