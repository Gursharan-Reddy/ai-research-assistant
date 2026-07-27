import React, { useState } from "react";
import "./App.css";

const API_BASE_URL = "https://ai-research-assistant-gx8t.onrender.com/api";

export default function DocumentAssistant() {
  const [file, setFile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState("");
  const [query, setQuery] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState({ text: "", type: "" });

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setStatusMessage({ text: "Uploading document...", type: "info" });

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setStatusMessage({ text: "Upload successful!", type: "success" });
        setFile(null);

        const uploadedDoc = data.document || {
          id: data.filename || file.name,
          filename: data.filename || file.name,
        };

        setDocuments((prev) => {
          const exists = prev.some((doc) => doc.id === uploadedDoc.id);
          return exists ? prev : [...prev, uploadedDoc];
        });

        setSelectedDocId(uploadedDoc.id);
      } else {
        const errData = await res.json();
        setStatusMessage({
          text: `Upload failed: ${errData.detail || "Server error"}`,
          type: "error",
        });
      }
    } catch (err) {
      console.error("Upload error:", err);
      setStatusMessage({ text: "Network error during upload.", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  const handleAskQuestion = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    if (!selectedDocId) {
      alert("Please select an active document first.");
      return;
    }

    const userQuestion = query;
    setQuery("");
    setChatHistory((prev) => [...prev, { sender: "user", text: userQuestion }]);
    setLoading(true);

    try {
      const payload = {
        filename: selectedDocId,
        question: userQuestion,
      };

      const res = await fetch(`${API_BASE_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        setChatHistory((prev) => [...prev, { sender: "ai", text: data.answer }]);
      } else {
        const errData = await res.json();
        setChatHistory((prev) => [
          ...prev,
          { sender: "ai", text: `Error: ${errData.detail || "Failed to retrieve response."}` },
        ]);
      }
    } catch (err) {
      console.error("Query error:", err);
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
      const res = await fetch(`${API_BASE_URL}/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: selectedDocId }),
      });

      if (res.ok) {
        const data = await res.json();
        setSummary(data.summary);
      } else {
        const errData = await res.json();
        setSummary(`Failed to generate summary: ${errData.detail || "Error"}`);
      }
    } catch (err) {
      console.error("Summarize error:", err);
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
                  const id = typeof doc === "string" ? doc : doc.id || doc.doc_id || idx;
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