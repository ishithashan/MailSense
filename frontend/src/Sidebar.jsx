function Sidebar({ activePage, onNavigate, userEmail }) {
  const navItems = [
    {
      id: "dashboard", label: "Dashboard",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
          <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
        </svg>
      )
    },
    {
      id: "inbox", label: "Inbox",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 8l10 7 10-7"/>
        </svg>
      )
    }
  ];

  const handleLogout = () => {
    window.location.href = "/"; // forces fresh login
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">📩</div>
        <span className="logo-text">RECMails</span>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(item => (
          <div
            key={item.id}
            className={`nav-item ${activePage === item.id ? "active" : ""}`}
            onClick={() => onNavigate(item.id)}
          >
            {item.icon}
            <span className="nav-label">{item.label}</span>
          </div>
        ))}

        {/* Logout */}
        <div className="nav-item logout" onClick={handleLogout}>
          Logout
        </div>
      </nav>

      {/* Bottom User Profile */}
      <div className="sidebar-footer">
        <div className="user-profile-card">
          <div className="avatar-wrapper">
            {/* If you eventually get a profile pic URL, you can swap this for an <img> */}
            <div className="avatar-circle">
              {userEmail ? userEmail[0].toUpperCase() : "U"}
              <div className="status-indicator"></div>
            </div>
          </div>
          
          <div className="user-info">
            <span className="user-name">{userEmail?.split('@')[0] || "User"}</span>
            <span className="user-email">{userEmail || "loading..."}</span>
          </div>

          <button className="profile-options-btn" title="Account Settings">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/>
            </svg>
          </button>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;