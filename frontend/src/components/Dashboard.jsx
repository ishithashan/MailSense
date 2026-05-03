import { useState, useEffect, useCallback } from "react";
import Sidebar from "../Sidebar";

// ── helpers ──────────────────────────────────────────────
const CATEGORY_META = {
  Placement: { cls: "cat-placement", priority: "High",   priorityCls: "priority-high",   color: "#10B981", bg: "#D1FAE5" },
  Academic:  { cls: "cat-academic",  priority: "Medium", priorityCls: "priority-medium", color: "#3B82F6", bg: "#DBEAFE" },
  Notices:   { cls: "cat-notices",   priority: "Medium", priorityCls: "priority-medium", color: "#F59E0B", bg: "#FEF3C7" },
  NPTEL:     { cls: "cat-nptel",     priority: "High",   priorityCls: "priority-high",   color: "#7C3AED", bg: "#EDE9FE" },
  GCR:       { cls: "cat-gcr",       priority: "Medium", priorityCls: "priority-medium", color: "#DB2777", bg: "#FCE7F3" },
  UiPath:    { cls: "cat-academic",  priority: "Low",    priorityCls: "priority-low",    color: "#3B82F6", bg: "#DBEAFE" },
  "Google Forms": { cls: "cat-others", priority: "Low",  priorityCls: "priority-low",    color: "#6B7280", bg: "#F3F4F6" },
  Others:    { cls: "cat-others",    priority: "Low",    priorityCls: "priority-low",    color: "#6B7280", bg: "#F3F4F6" },
  General:   { cls: "cat-others",    priority: "Low",    priorityCls: "priority-low",    color: "#6B7280", bg: "#F3F4F6" },
};

function catMeta(category) {
  return CATEGORY_META[category] || CATEGORY_META["Others"];
}

function getInitials(sender) {
  const name = sender.split("<")[0].trim() || sender;
  return name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase() || "?";
}

/*function formatCategory(cat) {
  if (!cat) return "Others";
  if (cat === "GCR") return "GCR";
  return cat.charAt(0).toUpperCase() + cat.slice(1).toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
}*/
function formatCategory(cat) {
  if (!cat) return "Others";
  if (cat === "GCR") return "GCR";
  if (cat === "NPTEL") return "Nptel";
  return cat.charAt(0).toUpperCase() + cat.slice(1).toLowerCase();
}

// ── Stat Card ─────────────────────────────────────────────
function StatCard({ icon, iconBg, iconColor, number, label, badge, badgeCls, extra }) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ background: iconBg }}>
        <svg viewBox="0 0 24 24" fill="none" stroke={iconColor} strokeWidth="2"
          strokeLinecap="round" strokeLinejoin="round" dangerouslySetInnerHTML={{ __html: icon }} />
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


// ── Main Dashboard ────────────────────────────────────────
function Dashboard() {
  const [activePage, setActivePage]   = useState("dashboard");
  const [emails, setEmails]           = useState([]);
  const [loading, setLoading]         = useState(false);
  const [filter, setFilter]           = useState("All");
  const [search, setSearch]           = useState("");
  const [lastSync, setLastSync]       = useState("--:--");
  const [userEmail, setUserEmail]     = useState("");

  // Fetch emails from Flask backend
  const fetchEmails = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/fetch_emails", {
  credentials: "include"
});
      if (res.redirected || res.status === 401) {
        window.location.href = "/api/login";
        return;
      }
      const data = await res.json();
      if (data.status === "success") {
        setEmails(data.emails || []);
        setUserEmail(data.user || "");
        const now = new Date();
        setLastSync(`${now.getHours().toString().padStart(2,"0")}:${now.getMinutes().toString().padStart(2,"0")} AM`);
      }
    } catch (err) {
      console.error("Fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

//  useEffect(() => {
//   fetchEmails();
// }, [fetchEmails]);

useEffect(() => {
  const loadEmails = async () => {
    await fetchEmails();
  };

  loadEmails();
}, [fetchEmails]);

  // Counts per category
  const counts = {
    total:     emails.length,
    placement: emails.filter(e => e.category === "Placement").length,
    academic:  emails.filter(e => ["Academic", "NPTEL", "GCR"].includes(e.category)).length,
    notices:   emails.filter(e => e.category === "Notices").length,
    others:    emails.filter(e => !["Placement","Academic","NPTEL","GCR","Notices"].includes(e.category)).length,
  };

  // Filter + search
  const visible = emails.filter(e => {
    const cat = e.category || "Others";
    const matchFilter =
      filter === "All"       ? true :
      filter === "Placement" ? cat === "Placement" :
      filter === "Academic"  ? ["Academic","NPTEL","GCR"].includes(cat) :
      filter === "Notices"   ? cat === "Notices" :
      filter === "Others"    ? !["Placement","Academic","NPTEL","GCR","Notices"].includes(cat) :
      true;
    const q = search.toLowerCase();
    const matchSearch = !q ||
      (e.sender || "").toLowerCase().includes(q) ||
      (e.subject || "").toLowerCase().includes(q) ||
      (e.body || "").toLowerCase().includes(q);
    return matchFilter && matchSearch;
  });

  const pills = ["All", "Placement", "Academic", "Notices", "Others"];
  const pillActiveClass = (p) => {
    if (filter !== p) return "";
    const map = { All: "active-all", Placement: "active-placement", Academic: "active-academic", Notices: "active-notices", Others: "active-others" };
    return map[p] || "active-all";
  };

  const avatarColors = ["#6C3BFF","#10B981","#3B82F6","#F59E0B","#EF4444","#DB2777","#7C3AED","#0EA5E9"];
  const avatarColor = (i) => avatarColors[i % avatarColors.length];

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
              <h1>Inbox Dashboard</h1>
              {/*<p>Smart email classification using Rule-Based + Naive Bayes ML</p>*/}
            </div>
            <div className="header-actions">
              <button className="btn btn-outline" onClick={fetchEmails} disabled={loading}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                </svg>
                Sync Emails
              </button>
              <button className="btn btn-primary" onClick={fetchEmails} disabled={loading}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                </svg>
                {loading ? "Refreshing..." : "Refresh"}
              </button>
            </div>
          </div>

          {/* Stat Cards */}
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

          {/* Email Table */}
          <div className="email-section">
            <div className="table-toolbar">
              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                <span className="filter-label">Filter by Category:</span>
                <div className="filter-pills">
                  {pills.map(p => (
                    <button
                      key={p}
                      className={`pill ${pillActiveClass(p)}`}
                      onClick={() => setFilter(p)}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
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
                    <th>Sender</th>
                    <th>Subject</th>
                    <th>Category</th>
                    <th>Priority</th>
                    <th>Received At</th>
                    <th>Action</th>
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
                      const cat = formatCategory(email.category || "Others");
                      const meta = catMeta(email.category || "Others");
                      const initials = getInitials(email.sender || "?");
                      const receivedAt = email.time ? `${email.time}` : (email.date || "—");
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
                              {email.body?.slice(0, 60) + (email.body?.length > 60 ? "..." : "") || ""}
                            </div>
                          </td>
                          <td>
                            <span className={`category-badge ${meta.cls}`}>{cat}</span>
                          </td>
                          <td>
                            <span className={`priority-badge ${meta.priorityCls}`}>
                              {meta.priority}
                            </span>
                          </td>
                          <td style={{ fontSize: "13px", color: "#6B7280" }}>{receivedAt}</td>
                          <td>
                            <div className="action-cell">
                              <button className="action-btn" title="View email">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                  <circle cx="12" cy="12" r="3"/>
                                </svg>
                              </button>
                              <button className="action-btn" title="Star email">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
          </div>

          {/* Workflow Diagram */}
          {/*<WorkflowDiagram />*/}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;