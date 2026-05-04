import "../App.css";

function HomePage() {
  return (
    <div className="home-container">
      {/* Navigation Bar */}
      <nav className="home-nav">
        <div className="logo-group">
          <div className="logo-icon-small">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <rect x="2" y="4" width="20" height="16" rx="2"/>
              <path d="M2 8l10 7 10-7"/>
            </svg>
          </div>
          <span className="logo-text">RECMails</span>
        </div>
        <a href="/api/login" className="nav-login-btn">Sign In</a>
      </nav>

      {/* Hero Section */}
      <main className="hero-section">
        <div className="hero-content">
          <div className="badge">New: AI-Powered Classification 2.0</div>
          <h1 className="hero-title">
            Tame your inbox with <span className="text-gradient">Intelligence.</span>
          </h1>
          <p className="hero-subtitle">
            RECMails automatically categorizes, prioritizes, and summarizes your 
            emails so you can focus on what actually matters.
          </p>

          <div className="cta-group">
            <a href="/api/login" className="btn-google-large">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Get Started with Google
            </a>
            <span className="trust-text">No credit card required.</span>
          </div>
        </div>

        {/* Visual Preview / Dashboard Mockup */}
        <div className="hero-visual">
          <div className="mockup-card">
            {/* Browser Header */}
            <div className="mockup-header">
              <div className="dot-group">
                <div className="dot red"></div>
                <div className="dot yellow"></div>
                <div className="dot green"></div>
              </div>
              <div className="mockup-search-bar">recmails.app/dashboard</div>
            </div>

            {/* Simulated Dashboard Content */}
            <div className="mockup-body">
              {/* Email Row 1 */}
              <div className="mockup-email-row active-row">
                <div className="mockup-avatar purple"></div>
                <div className="mockup-text-group">
                  <div className="skeleton-line sm"></div>
                  <div className="skeleton-line lg"></div>
                </div>
                <div className="skeleton-tag urgent">Placement</div>
              </div>

              {/* Email Row 2 */}
              <div className="mockup-email-row">
                <div className="mockup-avatar blue"></div>
                <div className="mockup-text-group">
                  <div className="skeleton-line sm"></div>
                  <div className="skeleton-line md"></div>
                </div>
                <div className="skeleton-tag info">Academic</div>
              </div>

              {/* Email Row 3 */}
              <div className="mockup-email-row">
                <div className="mockup-avatar green"></div>
                <div className="mockup-text-group">
                  <div className="skeleton-line sm"></div>
                  <div className="skeleton-line lg"></div>
                </div>
                <div className="skeleton-tag success">General</div>
              </div>

              {/* Floating Action Button Simulation */}
              <div className="mockup-fab"></div>
            </div>
          </div>

          {/* Decorative Background Blur */}
          <div className="hero-blur-circle"></div>
        </div>
      </main>
    </div>
  );
}

export default HomePage;