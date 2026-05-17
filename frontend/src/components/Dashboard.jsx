import { useState, useEffect, useCallback, useRef } from "react";
import Sidebar from "../Sidebar";

// ── helpers ──────────────────────────────────────────────
const CATEGORY_META = {
  Placement:      { cls: "cat-placement", priority: "High",   priorityCls: "priority-high",   color: "#10B981", bg: "#D1FAE5" },
  Academic:       { cls: "cat-academic",  priority: "Medium", priorityCls: "priority-medium", color: "#3B82F6", bg: "#DBEAFE" },
  Notices:        { cls: "cat-notices",   priority: "Medium", priorityCls: "priority-medium", color: "#F59E0B", bg: "#FEF3C7" },
  NPTEL:          { cls: "cat-nptel",     priority: "High",   priorityCls: "priority-high",   color: "#7C3AED", bg: "#EDE9FE" },
  GCR:            { cls: "cat-gcr",       priority: "Medium", priorityCls: "priority-medium", color: "#DB2777", bg: "#FCE7F3" },
  UiPath:         { cls: "cat-academic",  priority: "Low",    priorityCls: "priority-low",    color: "#3B82F6", bg: "#DBEAFE" },
  "Google Forms": { cls: "cat-others",    priority: "Low",    priorityCls: "priority-low",    color: "#6B7280", bg: "#F3F4F6" },
  Others:         { cls: "cat-others",    priority: "Low",    priorityCls: "priority-low",    color: "#6B7280", bg: "#F3F4F6" },
  General:        { cls: "cat-others",    priority: "Low",    priorityCls: "priority-low",    color: "#6B7280", bg: "#F3F4F6" },
  Digii:          { cls: "cat-notices",   priority: "High",   priorityCls: "priority-high",   color: "#F59E0B", bg: "#FEF3C7" },
  Newsletter:     { cls: "cat-others",    priority: "Low",    priorityCls: "priority-low",    color: "#6B7280", bg: "#F3F4F6" },
};

function catMeta(category) {
  return CATEGORY_META[category] || CATEGORY_META["Others"];
}

function getInitials(sender) {
  const name = sender.split("<")[0].trim() || sender;
  return name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase() || "?";
}

function formatCategory(cat) {
  if (!cat) return "Others";
  if (cat === "GCR") return "GCR";
  if (cat === "NPTEL") return "NPTEL";
  return cat.charAt(0).toUpperCase() + cat.slice(1).toLowerCase();
}

function getSmartActions(category) {
  const cat = category || "Others";
  if (cat === "Placement") return [
    { label: "📋 Save to Tracker", action: "tracker" },
    { label: "🔗 Find Company",    action: "company"  },
  ];
  if (cat === "Notices" || cat === "Digii") return [
    { label: "📅 Add Reminder", action: "reminder" },
    { label: "⚠️ Mark Urgent",  action: "urgent"   },
  ];
  if (["Academic", "NPTEL", "GCR", "UiPath"].includes(cat)) return [
    { label: "📚 Save to Notes",   action: "notes" },
    { label: "🗓 Schedule Study",  action: "study" },
  ];
  return [{ label: "🔖 Bookmark", action: "bookmark" }];
}

// ── Stat Card ─────────────────────────────────────────────
function StatCard({ icon, iconBg, iconColor, number, label, badge, badgeCls, extra }) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ background: iconBg }}>
        <svg viewBox="0 0 24 24" fill="none" stroke={iconColor} strokeWidth="2"
          strokeLinecap="round" strokeLinejoin="round"
          dangerouslySetInnerHTML={{ __html: icon }} />
      </div>
      <div className="stat-info">
        <div className="stat-number" style={{ color: iconColor }}>{number}</div>
        <div className="stat-label">{label}</div>
        {badge && <span className={`stat-badge ${badgeCls}`}>{badge}</span>}
        {extra && <div style={{ fontSize: "11px", color: "#10B981", marginTop: "2px", fontWeight: 600 }}>{extra}</div>}
      </div>
    </div>
  );
}

// ── Dot Loader ────────────────────────────────────────────
function DotLoader({ text }) {
  return (
    <div className="ai-generating">
      <div className="summary-dots">
        <span /><span /><span />
      </div>
      <p>{text}</p>
    </div>
  );
}

// ── AI Summary Panel ──────────────────────────────────────
function AISummaryPanel({ summary, loading, onRegenerate }) {
  if (loading) return <DotLoader text="Reading email and generating summary..." />;

  if (summary) {
    return (
      <div className="summary-card">
        <div className="summary-icon">✨</div>
        <div className="summary-text">{summary}</div>
        <button className="summarize-btn" style={{ marginTop: "12px" }} onClick={onRegenerate}>
          🔄 Regenerate
        </button>
      </div>
    );
  }

  return <DotLoader text="Generating summary..." />;
}

// ── Quick Reply Panel ─────────────────────────────────────
function QuickReplyPanel({ reply, loading, sender, subject, onRedraft }) {
  const textareaRef = useRef(null);

  if (loading) return <DotLoader text="Drafting a reply for you..." />;

  if (reply) {
    return (
      <div className="reply-card">
        <div className="reply-meta">
          <span>To: {sender}</span>
          <span>Re: {subject}</span>
        </div>
        <textarea
          ref={textareaRef}
          className="reply-textarea"
          defaultValue={reply}
          rows={8}
        />
        <div className="reply-actions">
          <button className="btn btn-outline btn-sm" onClick={onRedraft}>
            🔄 Redraft
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={() => {
              const text = textareaRef.current?.value || reply;
              navigator.clipboard?.writeText(text);
              alert("Reply copied to clipboard!");
            }}
          >
            📋 Copy Reply
          </button>
        </div>
      </div>
    );
  }

  return <DotLoader text="Drafting reply..." />;
}

// ── Main Dashboard ────────────────────────────────────────
function Dashboard() {
  const [activePage, setActivePage]       = useState("dashboard");
  const [emails, setEmails]               = useState([]);
  const [loading, setLoading]             = useState(false);
  const [filter, setFilter]               = useState("All");
  const [search, setSearch]               = useState("");
  const [lastSync, setLastSync]           = useState("--:--");
  const [userEmail, setUserEmail]         = useState("");
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [emailBody, setEmailBody]         = useState("");
  const [activeTab, setActiveTab]         = useState("body");

  // AI states
  const [aiSummary, setAiSummary]           = useState("");
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [aiReply, setAiReply]               = useState("");
  const [replyLoading, setReplyLoading]     = useState(false);

  // ── Fetch all emails ──────────────────────────────────────
  

  // ── Fetch all emails ──────────────────────────────────────
  const fetchEmails = useCallback(async () => {
    try {
      const res = await fetch("/api/fetch_emails", { credentials: "include" });
      if (res.redirected || res.status === 401) {
        window.location.href = "/api/login";
        return;
      }
      const data = await res.json();
      if (data.status === "success") {
        setEmails(data.emails || []);
        setUserEmail(data.user || "");
        
        const now = new Date();
        const h = now.getHours();
        const m = now.getMinutes().toString().padStart(2, "0");
        setLastSync(`${(h % 12 || 12).toString().padStart(2, "0")}:${m} ${h >= 12 ? "PM" : "AM"}`);
      }
    } catch (err) {
      console.error("Fetch error:", err);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    const initialize = async () => {
      setLoading(true);
      try {
        await fetchEmails();
      } finally {
        setLoading(false);
      }
    };

    void initialize();
  }, [fetchEmails]);   // ← fetchEmails is stable thanks to useCallback

  // ── Fetch single email body ───────────────────────────────
  const fetchSingleEmail = async (id) => {
    try {
      const res = await fetch(`/api/email/${id}`, { credentials: "include" });
      const data = await res.json();
      if (data.status === "success") setEmailBody(data.body);
    } catch {
      // silent fail
    }
  };

  // ── AI Summary ───────────────────────────────────────────
  const generateSummary = useCallback(async (email, body) => {
    setSummaryLoading(true);
    try {
      const res = await fetch("/api/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          subject:  email?.subject  || "",
          body:     body || email?.body || "",
          category: email?.category || "General",
        }),
      });
      const data = await res.json();
      setAiSummary(data.status === "success" ? data.summary : "Could not generate summary. Please try again.");
    } catch {
      setAiSummary("Error reaching summary service.");
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  // ── AI Quick Reply ────────────────────────────────────────
  const generateReply = useCallback(async (email, body) => {
    setReplyLoading(true);
    try {
      const res = await fetch("/api/draft_reply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          subject:  email?.subject  || "",
          body:     body || email?.body || "",
          sender:   email?.sender   || "",
          category: email?.category || "General",
        }),
      });
      const data = await res.json();
      setAiReply(data.status === "success" ? data.reply : "Could not draft reply. Please try again.");
    } catch {
      setAiReply("Error reaching reply service.");
    } finally {
      setReplyLoading(false);
    }
  }, []);

  const closeModal = () => {
    setSelectedEmail(null);
    setEmailBody("");
    setAiSummary("");
    setAiReply("");
    setActiveTab("body");
  };

  const openEmail = (email) => {
    setSelectedEmail(email);
    setAiSummary("");
    setAiReply("");
    setActiveTab("body");
    void fetchSingleEmail(email.id);
  };

  const toggleStar = async (emailId) => {
    try {
      const res = await fetch(`/api/email/${emailId}/star`, {
        method: "POST",
        credentials: "include",
      });
      
      if (res.ok) {
        // Refresh emails to update UI
        await fetchEmails();
      } else {
        alert("Failed to star email");
      }
    } catch (err) {
      console.error(err);
      alert("Failed to star email");
    }
  };

  // ── Tab switch helper (triggers AI lazily) ────────────────
  const switchTab = (tab) => {
    setActiveTab(tab);
    if (tab === "summary" && !aiSummary && !summaryLoading) {
      void generateSummary(selectedEmail, emailBody);
    }
    if (tab === "reply" && !aiReply && !replyLoading) {
      void generateReply(selectedEmail, emailBody);
    }
  };

  // ── Counts + filter ───────────────────────────────────────
  const counts = {
    total:     emails.length,
    placement: emails.filter(e => e.category === "Placement").length,
    academic:  emails.filter(e => ["Academic", "NPTEL", "GCR"].includes(e.category)).length,
    notices:   emails.filter(e => ["Notices", "Digii"].includes(e.category)).length,
    others:    emails.filter(e => !["Placement","Academic","NPTEL","GCR","Notices","Digii"].includes(e.category)).length,
  };

  const visible = activePage !== "dashboard" ? emails : emails.filter(e => {
    const cat = e.category || "Others";
    const matchFilter =
      filter === "All"       ? true :
      filter === "Placement" ? cat === "Placement" :
      filter === "Academic"  ? ["Academic","NPTEL","GCR"].includes(cat) :
      filter === "Notices"   ? ["Notices","Digii"].includes(cat) :
      filter === "Others"    ? !["Placement","Academic","NPTEL","GCR","Notices","Digii"].includes(cat) :
      true;
    const q = search.toLowerCase();
    const matchSearch = !q ||
      (e.sender  || "").toLowerCase().includes(q) ||
      (e.subject || "").toLowerCase().includes(q) ||
      (e.body    || "").toLowerCase().includes(q);
    return matchFilter && matchSearch;
  });

  const pills = ["All", "Placement", "Academic", "Notices", "Others"];
  const pillActiveClass = (p) => {
    if (filter !== p) return "";
    return { All: "active-all", Placement: "active-placement", Academic: "active-academic", Notices: "active-notices", Others: "active-others" }[p] || "active-all";
  };

  const avatarColors = ["#6C3BFF","#10B981","#3B82F6","#F59E0B","#EF4444","#DB2777","#7C3AED","#0EA5E9"];
  const avatarColor  = (i) => avatarColors[i % avatarColors.length];

  // ──────────────────────────────────────────────────────────
  return (
    <div className="app-layout">
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        systemStatus={{ emailCount: counts.total, lastUpdated: lastSync }}
      />

      <div className="main-area">
        {/* Topbar */}
        <header className="topbar">
          <div className="topbar-left">
            <button className="hamburger">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
              </svg>
            </button>
          </div>
          <div className="topbar-right">
            <div className="sync-info">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
              </svg>
              Last Sync: {lastSync}
            </div>
            <div className="user-avatar" title={userEmail}>
              {userEmail ? userEmail[0].toUpperCase() : "U"}
            </div>
          </div>
        </header>

        <div className="page-content">
          {/* Page Header */}
          <div className="page-header">
            <div>
              <h1>{activePage === "dashboard" ? "Dashboard" : "Inbox"}</h1>
            </div>
            {activePage === "dashboard" && (
              <div className="header-actions">
                <button 
                  className="btn btn-outline" 
                  onClick={async () => {
                    setLoading(true);
                    try {
                      await fetchEmails();
                    } finally {
                      setLoading(false);
                    }
                  }} 
                  disabled={loading}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
                    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                  </svg>
                  Sync Emails
                </button>
                <button className="btn btn-primary" onClick={async () => {
                  setLoading(true);
                  try {
                    await fetchEmails();
                  } finally {
                    setLoading(false);
                  }
                }} disabled={loading}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
                    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                  </svg>
                  {loading ? "Refreshing..." : "Refresh"}
                </button>
              </div>
            )}
          </div>

          {/* Stat Cards */}
          {activePage === "dashboard" && (
            <div className="stat-cards">
              <StatCard
                icon='<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 8l10 7 10-7"/>'
                iconBg="#EDE9FE" iconColor="#6C3BFF"
                number={counts.total} label="Total Emails"
                extra={counts.total > 0 ? `+${Math.min(counts.total, 12)} new` : ""}
              />
              <StatCard
                icon='<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/><line x1="12" y1="12" x2="12" y2="16"/><line x1="10" y1="14" x2="14" y2="14"/>'
                iconBg="#D1FAE5" iconColor="#10B981"
                number={counts.placement} label="Placement"
                badge="High Priority" badgeCls="priority-high"
              />
              <StatCard
                icon='<path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>'
                iconBg="#DBEAFE" iconColor="#3B82F6"
                number={counts.academic} label="Academic"
                badge="Medium Priority" badgeCls="priority-medium"
              />
              <StatCard
                icon='<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>'
                iconBg="#FEF3C7" iconColor="#F59E0B"
                number={counts.notices} label="Notices"
                badge="Medium Priority" badgeCls="priority-medium"
              />
              <StatCard
                icon='<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/>'
                iconBg="#F3F4F6" iconColor="#6B7280"
                number={counts.others} label="Others"
                badge="Low Priority" badgeCls="priority-low"
              />
            </div>
          )}

          {/* Email Table */}
          <div className="email-section">
            <div className="table-toolbar">
              {activePage === "dashboard" && (
                <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                  <span className="filter-label">Filter by Category:</span>
                  <div className="filter-pills">
                    {pills.map(p => (
                      <button key={p} className={`pill ${pillActiveClass(p)}`} onClick={() => setFilter(p)}>
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <div className="search-box">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <input
                  placeholder="Search emails..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
              </div>
            </div>

            {loading ? (
              <div className="loading-state">
                <div className="spinner" />
                <span>Fetching and classifying emails...</span>
              </div>
            ) : (
              <table className="email-table">
                <thead>
                  <tr>
                    <th>Sender</th><th>Subject</th><th>Category</th>
                    <th>Priority</th><th>Received At</th><th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.length === 0 ? (
                    <tr>
                      <td colSpan={6}>
                        <div className="loading-state">
                          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 8l10 7 10-7"/>
                          </svg>
                          <span>{emails.length === 0 ? "Click Sync Emails to load your inbox" : "No emails match this filter"}</span>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    visible.map((email, i) => {
                      const cat  = formatCategory(email.category || "Others");
                      const meta = catMeta(email.category || "Others");
                      const initials = getInitials(email.sender || "?");
                      return (
                        <tr key={i}>
                          <td>
                            <div className="sender-cell">
                              <div className="sender-avatar" style={{ background: avatarColor(i) }}>
                                {initials[0]}
                              </div>
                              <span className="sender-email">
                                {email.sender?.replace(/<.*>/, "").trim() || email.sender}
                              </span>
                            </div>
                          </td>
                          <td className="subject-cell">
                            <div className="subject-main">{email.subject || "(No Subject)"}</div>
                            <div className="subject-snippet">
                              {(email.body || "").slice(0, 60) + (email.body?.length > 60 ? "..." : "")}
                            </div>
                          </td>
                          <td><span className={`category-badge ${meta.cls}`}>{cat}</span></td>
                          <td><span className={`priority-badge ${meta.priorityCls}`}>{meta.priority}</span></td>
                          <td style={{ fontSize: "13px", color: "#6B7280" }}>{email.time || ""}</td>
                          <td>
                            <div className="action-cell">
                              <button className="action-btn" title="View email" onClick={() => openEmail(email)}>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                  <circle cx="12" cy="12" r="3"/>
                                </svg>
                              </button>
                              <button 
                                className="action-btn" 
                                title="Star email"
                                onClick={() => toggleStar(email.id)}
                                style={{ color: email.labelIds?.includes('STARRED') ? '#facc15' : '#6B7280' }}
                              >
                                <svg 
                                  viewBox="0 0 24 24" 
                                  fill={email.labelIds?.includes('STARRED') ? "#facc15" : "none"} 
                                  stroke="currentColor" 
                                  strokeWidth="2" 
                                  strokeLinecap="round" 
                                  strokeLinejoin="round"
                                >
                                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                                </svg>
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            )}

            {/* ── Email Modal ──────────────────────────────────── */}
            {selectedEmail && (
              <div className="modal-overlay" onClick={closeModal}>
                <div className="email-card-popup email-card-popup--wide" onClick={e => e.stopPropagation()}>

                  {/* Header */}
                  <div className="modal-header">
                    <div className="modal-header-left">
                      <div className="modal-avatar" style={{ background: avatarColor(emails.indexOf(selectedEmail)) }}>
                        {getInitials(selectedEmail.sender)[0]}
                      </div>
                      <div>
                        <h3>{selectedEmail.subject || "(No Subject)"}</h3>
                        <p className="modal-subtitle">From: <span>{selectedEmail.sender}</span></p>
                      </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span className={`category-badge ${catMeta(selectedEmail.category).cls}`} style={{ fontSize: "11px" }}>
                        {formatCategory(selectedEmail.category || "Others")}
                      </span>
                      <button className="close-icon-btn" onClick={closeModal}>
                        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
                          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Tab bar */}
                  <div className="modal-tabs">
                    <button className={`modal-tab ${activeTab === "body"    ? "modal-tab--active" : ""}`} onClick={() => setActiveTab("body")}>
                      📧 Email
                    </button>
                    <button className={`modal-tab ${activeTab === "summary" ? "modal-tab--active" : ""}`} onClick={() => switchTab("summary")}>
                      ✨ Summary {aiSummary && <span className="tab-dot" />}
                    </button>
                    <button className={`modal-tab ${activeTab === "reply"   ? "modal-tab--active" : ""}`} onClick={() => switchTab("reply")}>
                      ↩ Quick Reply {aiReply && <span className="tab-dot" />}
                    </button>
                    <button className={`modal-tab ${activeTab === "actions" ? "modal-tab--active" : ""}`} onClick={() => setActiveTab("actions")}>
                      ⚡ Actions
                    </button>
                  </div>

                  {/* Tab content */}
                  <div className="modal-body-container">

                    {/* ── Body tab ── */}
                    {activeTab === "body" && (
                      emailBody ? (
                        <div className="email-body-content" dangerouslySetInnerHTML={{ __html: emailBody }} />
                      ) : (
                        <div className="loading-body">
                          <div className="spinner-small" />
                          <span>Loading content...</span>
                        </div>
                      )
                    )}

                    {/* ── Summary tab — uses AISummaryPanel ── */}
                    {activeTab === "summary" && (
                      <div className="tab-panel">
                        <AISummaryPanel
                          summary={aiSummary}
                          loading={summaryLoading}
                          onRegenerate={() => {
                            setAiSummary("");
                            void generateSummary(selectedEmail, emailBody);
                          }}
                        />
                      </div>
                    )}

                    {/* ── Reply tab — uses QuickReplyPanel ── */}
                    {activeTab === "reply" && (
                      <div className="tab-panel">
                        <QuickReplyPanel
                          reply={aiReply}
                          loading={replyLoading}
                          sender={selectedEmail.sender}
                          subject={selectedEmail.subject}
                          onRedraft={() => {
                            setAiReply("");
                            void generateReply(selectedEmail, emailBody);
                          }}
                        />
                      </div>
                    )}

                    {/* ── Actions tab ── */}
                    {activeTab === "actions" && (
                      <div className="tab-panel">
                        <div className="smart-actions-grid">
                          <p className="smart-actions-title">
                            Smart Actions for <strong>{formatCategory(selectedEmail.category)}</strong> email
                          </p>
                          {getSmartActions(selectedEmail.category).map((a, i) => (
                            <button
                              key={i}
                              className="smart-action-btn"
                              onClick={() => alert(`"${a.label}" — connect your calendar/tracker here!`)}
                            >
                              {a.label}
                            </button>
                          ))}
                          <button
                            className="smart-action-btn smart-action-btn--summary"
                            onClick={() => switchTab("summary")}
                          >
                            ✨ AI Summary
                          </button>
                          <button
                            className="smart-action-btn smart-action-btn--reply"
                            onClick={() => switchTab("reply")}
                          >
                            ↩ Draft Reply
                          </button>
                          <a
                            href="https://mail.google.com/"
                            target="_blank"
                            rel="noreferrer"
                            className="smart-action-btn smart-action-btn--gmail"
                          >
                            📬 Open in Gmail
                          </a>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Footer */}
                  <div className="modal-footer">
                    <span style={{ fontSize: "12px", color: "#9CA3AF" }}>{selectedEmail.time || ""}</span>
                    <div style={{ display: "flex", gap: "8px" }}>
                      <button className="btn btn-outline" onClick={closeModal}>Close</button>
                      <button className="btn btn-primary" onClick={() => switchTab("reply")}>
                        ↩ Reply
                      </button>
                    </div>
                  </div>

                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
