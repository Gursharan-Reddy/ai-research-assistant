import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = "https://ai-research-assistant-gx8t.onrender.com/api";

export default function App() {
  const [file, setFile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);

  const [summary, setSummary] = useState('');
  const [summaryError, setSummaryError] = useState('');

  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return alert('Please select a file to upload.');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_BASE}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const uploadedDoc = res.data.document || {
        id: res.data.filename || file.name,
        filename: res.data.filename || file.name,
      };

      setDocuments((prev) => {
        const exists = prev.some((doc) => doc.id === uploadedDoc.id);
        return exists ? prev : [...prev, uploadedDoc];
      });

      setSelectedDocId(uploadedDoc.id);
      setFile(null);
    } catch (err) {
      console.error('Upload Error:', err);
      alert('Failed to upload document.');
    }
  };

  const handleSummarize = async () => {
    if (!selectedDocId) {
      setSummaryError('Please select a document to summarize.');
      setSummary('');
      return;
    }

    try {
      setSummaryError('');
      const res = await axios.post(`${API_BASE}/summarize`, { 
        filename: selectedDocId 
      });
      setSummary(res.data.summary);
    } catch (err) {
      console.error('Summarize Error:', err);
      setSummary('');
      if (err.response && err.response.status === 404) {
        setSummaryError('Failed to generate summary: Document not found.');
      } else {
        setSummaryError('An error occurred while generating summary.');
      }
    }
  };

  const handleAskQuestion = async (e) => {
    if (e) e.preventDefault();
    if (!question.trim()) return;
    if (!selectedDocId) return alert('Please select an active document first.');

    const userMessage = question;
    setQuestion('');

    setChatHistory((prev) => [...prev, { sender: 'You', text: userMessage }]);
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/query`, {
        filename: selectedDocId,
        question: userMessage,
      });

      setChatHistory((prev) => [
        ...prev,
        { sender: 'AI Assistant', text: res.data.answer },
      ]);
    } catch (err) {
      console.error('Query Error:', err);
      const errorMsg = err.response?.data?.detail || 'Error: Processing request failed.';
      setChatHistory((prev) => [
        ...prev,
        { sender: 'AI Assistant', text: errorMsg },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h2>AI Research & Knowledge Assistant</h2>

      <div className="layout">
        {/* Left Sidebar */}
        <div className="sidebar">
          <div className="card">
            <h3>Upload Document</h3>
            <input type="file" onChange={handleFileChange} accept=".pdf" />
            <button onClick={handleUpload}>Upload PDF</button>
          </div>

          <div className="card">
            <h3>Active Documents</h3>
            <ul className="doc-list">
              {documents.length === 0 ? (
                <li style={{ color: '#94a3b8', cursor: 'default' }}>
                  No documents uploaded yet.
                </li>
              ) : (
                documents.map((doc) => (
                  <li
                    key={doc.id}
                    className={selectedDocId === doc.id ? 'active' : ''}
                    onClick={() => setSelectedDocId(doc.id)}
                  >
                    📄 {doc.filename}
                  </li>
                ))
              )}
            </ul>
            <button onClick={handleSummarize}>Summarize Selected</button>
          </div>
        </div>

        {/* Right Content Area */}
        <div className="main">
          {/* Summary Box */}
          <div className="card">
            <h3>Document Summary</h3>
            {summaryError && <p className="error">{summaryError}</p>}
            {summary ? (
              <p className="summary-text">{summary}</p>
            ) : (
              !summaryError && (
                <p className="summary-text" style={{ color: '#94a3b8' }}>
                  Select an active document and click "Summarize Selected".
                </p>
              )
            )}
          </div>

          {/* RAG Chat Box */}
          <div className="card chat-card">
            <h3>RAG Question Answering</h3>
            <div className="chat-window">
              {chatHistory.length === 0 ? (
                <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
                  Ask any question about your active document to get started.
                </p>
              ) : (
                chatHistory.map((chat, idx) => (
                  <div
                    key={idx}
                    className={`chat-bubble ${chat.sender === 'You' ? 'user' : 'ai'}`}
                  >
                    <strong>{chat.sender}:</strong>
                    <p>{chat.text}</p>
                  </div>
                ))
              )}
              {loading && <div className="chat-bubble ai">AI Assistant is typing...</div>}
            </div>

            <form className="chat-input" onSubmit={handleAskQuestion}>
              <input
                type="text"
                placeholder="Ask a question about the document..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
              />
              <button type="submit" disabled={loading}>
                Ask
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}