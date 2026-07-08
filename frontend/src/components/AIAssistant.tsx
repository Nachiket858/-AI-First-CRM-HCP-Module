import React, { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from '../store';
import { sendMessageToAgent, addUserMessage, clearChat } from '../slices/chatSlice';
import { Send, Sparkles, Database, Trash2, Cpu } from 'lucide-react';

export const AIAssistant: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { messages, toolLogs, isTyping } = useSelector((state: RootState) => state.chat);
  const formData = useSelector((state: RootState) => state.interaction.formData);

  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Suggestions for testing the tools
  const suggestions = [
    { text: 'Log meeting with Dr. Sarah Jenkins', query: 'Today I met with Dr. Sarah Jenkins and discussed Prodo-X efficacy. Sentiment was positive.' },
    { text: 'Look up Dr. Jenkins profile', query: 'Can you tell me about Dr. Sarah Jenkins specialty and preferences?' },
    { text: 'Update sentiment to Neutral', query: 'Actually, change the sentiment to Neutral.' },
    { text: 'Search for Prodo materials', query: 'Search for brochures related to Prodo.' },
    { text: 'Suggest follow-up action', query: 'Suggest follow-up actions based on the topics we discussed.' },
    { text: 'Email materials to doctor', query: 'Please email the shared brochures to the doctor.' }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = () => {
    if (!input.trim() || isTyping) return;
    
    const query = input;
    setInput('');
    
    // 1. Add user message locally
    dispatch(addUserMessage(query));
    
    // 2. Format message history for LLM context
    const chatHistory = messages.map(m => ({ sender: m.sender, text: m.text }));
    
    // 3. Dispatch to agent backend
    dispatch(
      sendMessageToAgent({
        text: query,
        formState: formData,
        history: chatHistory,
      })
    );
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (query: string) => {
    setInput(query);
  };

  // Helper to parse simple markdown to HTML elements
  const formatMarkdown = (text: string) => {
    // 1. Split lines
    const lines = text.split('\n');
    let insideList = false;
    const elements: React.ReactNode[] = [];

    lines.forEach((line, idx) => {
      // Check if bullet point
      const isBullet = line.trim().startsWith('- ') || line.trim().startsWith('* ');
      
      let content = line;
      if (isBullet) {
        content = line.trim().substring(2);
      }

      // Parse bold tags **text**
      const parts = content.split('**');
      const formattedParts = parts.map((part, pIdx) => {
        if (pIdx % 2 === 1) {
          return <strong key={pIdx} style={{ color: '#60a5fa', fontWeight: 600 }}>{part}</strong>;
        }
        return part;
      });

      if (isBullet) {
        if (!insideList) {
          insideList = true;
        }
        elements.push(
          <li key={`line-${idx}`} style={{ marginLeft: '16px', marginBottom: '4px' }}>
            {formattedParts}
          </li>
        );
      } else {
        insideList = false;
        elements.push(
          <div key={`line-${idx}`} style={{ marginBottom: '6px' }}>
            {formattedParts}
          </div>
        );
      }
    });

    return <div className="message-content">{elements}</div>;
  };

  return (
    <div className="assistant-panel">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-title">
          <Sparkles size={16} style={{ color: '#60a5fa' }} />
          <div>
            <div>AI Assistant</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 400 }}>
              Log interaction details here via chat
            </div>
          </div>
        </div>
        <button
          className="btn-secondary"
          style={{ padding: '6px 10px', fontSize: '0.75rem' }}
          onClick={() => dispatch(clearChat())}
          title="Clear Chat History"
        >
          <Trash2 size={12} /> Clear
        </button>
      </div>

      {/* Message Feed */}
      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-bubble ${msg.sender}`}>
            {msg.sender === 'assistant' ? (
              formatMarkdown(msg.text)
            ) : (
              <div>{msg.text}</div>
            )}
            <div
              style={{
                fontSize: '0.7rem',
                color: msg.sender === 'user' ? 'rgba(255,255,255,0.7)' : 'var(--text-muted)',
                textAlign: 'right',
                marginTop: '6px',
              }}
            >
              {msg.timestamp}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="message-bubble assistant" style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--text-muted)', animation: 'soundWave 1s infinite alternate' }} />
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--text-muted)', animation: 'soundWave 1s infinite alternate', animationDelay: '0.2s' }} />
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--text-muted)', animation: 'soundWave 1s infinite alternate', animationDelay: '0.4s' }} />
          </div>
        )}

        {/* Real-time Tool Call logs Visualization */}
        {toolLogs && toolLogs.length > 0 && (
          <div style={{ marginTop: '15px', borderTop: '1px solid var(--border-color)', paddingTop: '15px' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Cpu size={14} style={{ color: '#10b981' }} /> LangGraph Tool Executions:
            </div>
            <div className="tool-logs-container">
              {toolLogs.map((log, idx) => (
                <div key={idx} className="tool-log-item">
                  <div className="tool-log-details">
                    <Database size={12} className="tool-log-icon" />
                    <span className="tool-log-text">{log.tool_name}()</span>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: '#6ee7b7', background: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                    Success
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestion Chips */}
      <div className="suggestion-chips">
        {suggestions.map((sug, idx) => (
          <div
            key={idx}
            className="suggestion-chip"
            onClick={() => handleSuggestionClick(sug.query)}
          >
            {sug.text}
          </div>
        ))}
      </div>

      {/* Chat Input */}
      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <textarea
            className="chat-input"
            rows={1}
            placeholder="Describe Interaction..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
          />
          <button className="chat-send-btn" onClick={handleSend} disabled={isTyping}>
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};
