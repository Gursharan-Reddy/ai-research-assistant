import React, { useState, useEffect } from "react";
import "./App.css";

const API_BASE_URL = "http://localhost:8000";

export default function DocumentAssistant() {
  const [file, setFile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState("");
  const [query, setQuery] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState({ text: "", type: "" });

  // Fetch documents list on initial mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/documents/list`);
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || data || []);
      }
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setStatusMessage({ text: "Uploading document...", type: "info" });

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE_URL}/documents/upload`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setStatusMessage({ text: "Upload successful!", type: "success" });
        setFile(null);
        fetchDocuments(); // Refresh document list
        if (data.doc_id) {
          setSelectedDocId(data.doc_id);
        }
      } else {
        const errData = await res.json();
        setStatusMessage({
          text: `Upload failed: ${errData.detail || "Server error"}`,
          type: "error",
        });
      }
    } catch (err) {
      setStatusMessage({ text: "Network error during upload.", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  const handleAskQuestion = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userQuestion = query;
    setQuery("");
    setChatHistory((prev) => [...prev, { sender: "user", text: userQuestion }]);
    setLoading(true);

    try {
      const payload = {
        query: userQuestion,
        search_mode: "hybrid",
      };
      if (selectedDocId) {
        payload.doc_id = selectedDocId;
      }

      const res = await fetch(`${API_BASE_URL}/search/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        const answerText = data.answer || data.response || JSON.stringify(data);
        setChatHistory((prev) => [...prev, { sender: "ai", text: answerText }]);
      } else {
        const errData = await res.json();
        setChatHistory((prev) => [
          ...prev,
          { sender: "ai", text: `Error: ${errData.detail || "Failed to retrieve response."}` },
        ]);
      }
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        { sender: "ai", text: "Network error connecting to backend API." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleGetSummary = async () => {
    if (!selectedDocId) {
      alert("Please select a document from the list first.");
      return;
    }

    setLoading(true);
    setSummary("");

    try {
      const res = await fetch(`${API_BASE_URL}/analysis/summarize/${selectedDocId}`);
      if (res.ok) {
        const data = await res.json();
        setSummary(data.summary || data.result || JSON.stringify(data, null, 2));
      } else {
        const errData = await res.json();
        setSummary(`Failed to generate summary: ${errData.detail || "Error"}`);
      }
    } catch (err) {
      setSummary("Network error requesting summary.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h1>AI Research & Knowledge Assistant</h1>
        <p>Upload technical documents and perform RAG-powered queries or analysis</p>
      </header>

      {statusMessage.text && (
        <div className={`status-banner ${statusMessage.type}`}>
          {statusMessage.text}
        </div>
      )}

      <div className="layout-grid">
        {/* Sidebar Panel */}
        <aside className="sidebar">
          <section className="card">
            <h2>Upload Document</h2>
            <form onSubmit={handleFileUpload} className="upload-form">
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setFile(e.target.files[0])}
                className="file-input"
              />
              <button type="submit" disabled={!file || loading} className="btn primary-btn">
                {loading ? "Uploading..." : "Upload PDF"}
              </button>
            </form>
          </section>

          <section className="card">
            <h2>Active Documents</h2>
            {documents.length === 0 ? (
              <p className="empty-text">No documents uploaded yet.</p>
            ) : (
              <ul className="doc-list">
                {documents.map((doc, idx) => {
                  const id = typeof doc === "string" ? doc : doc.doc_id || doc.id || idx;
                  const name = doc.filename || doc.name || `Document ${id}`;
                  return (
                    <li
                      key={id}
                      className={`doc-item ${selectedDocId === id ? "active" : ""}`}
                      onClick={() => setSelectedDocId(id)}
                    >
                      <span className="doc-icon">📄</span>
                      <span className="doc-name">{name}</span>
                    </li>
                  );
                })}
              </ul>
            )}
            <button
              onClick={handleGetSummary}
              disabled={!selectedDocId || loading}
              className="btn secondary-btn"
              style={{ marginTop: "12px", width: "100%" }}
            >
              Summarize Selected
            </button>
          </section>
        </aside>

        {/* Main Workspace Panel */}
        <main className="main-content">
          {/* Summary Box */}
          {summary && (
            <section className="card summary-box">
              <h2>Document Summary</h2>
              <pre className="summary-text">{summary}</pre>
            </section>
          )}

          {/* RAG Chat Window */}
          <section className="card chat-card">
            <h2>RAG Question Answering</h2>
            <div className="chat-window">
              {chatHistory.length === 0 ? (
                <div className="chat-placeholder">
                  Ask any question about your uploaded document to test retrieval...
                </div>
              ) : (
                chatHistory.map((msg, idx) => (
                  <div key={idx} className={`chat-bubble ${msg.sender}`}>
                    <strong>{msg.sender === "user" ? "You" : "AI Assistant"}:</strong>
                    <p>{msg.text}</p>
                  </div>
                ))
              )}
            </div>

            <form onSubmit={handleAskQuestion} className="chat-input-form">
              <input
                type="text"
                placeholder="Ask a question about the document..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="text-input"
                disabled={loading}
              />
              <button type="submit" disabled={!query.trim() || loading} className="btn primary-btn">
                Ask
              </button>
            </form>
          </section>
        </main>
      </div>
    </div>
  );
}