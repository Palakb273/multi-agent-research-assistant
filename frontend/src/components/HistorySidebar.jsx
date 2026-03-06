/**
 * HistorySidebar.jsx — Research History Sidebar
 * ===============================================
 * WHY THIS COMPONENT:
 * Users want to revisit past research. The sidebar shows a chronological
 * list of all research sessions stored in Supabase.
 */

function HistorySidebar({ history, activeId, onSelect, onNewResearch, userEmail, onLogout }) {
    const formatDate = (dateStr) => {
        try {
            const date = new Date(dateStr)
            const now = new Date()
            const diffMs = now - date
            const diffMins = Math.floor(diffMs / 60000)
            const diffHours = Math.floor(diffMs / 3600000)
            const diffDays = Math.floor(diffMs / 86400000)

            if (diffMins < 1) return 'Just now'
            if (diffMins < 60) return `${diffMins}m ago`
            if (diffHours < 24) return `${diffHours}h ago`
            if (diffDays < 7) return `${diffDays}d ago`
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        } catch {
            return ''
        }
    }

    return (
        <aside className="sidebar" id="history-sidebar">
            {/* Sidebar Header */}
            <div className="sidebar-header">
                <div className="sidebar-logo">
                    <span className="logo-icon">🔬</span>
                    <h2>ResearchAI</h2>
                </div>
            </div>

            {/* Sidebar Content */}
            <div className="sidebar-content">
                {/* New Research Button */}
                <button
                    className="new-research-btn"
                    onClick={onNewResearch}
                    id="sidebar-new-research"
                >
                    <span>+</span>
                    <span>New Research</span>
                </button>

                {/* History Section */}
                <div className="sidebar-section-title">Recent Research</div>

                {history.length === 0 ? (
                    <div className="empty-history">
                        <div className="empty-icon">📚</div>
                        <p>No research history yet.<br />Start your first research!</p>
                    </div>
                ) : (
                    history.map((item) => (
                        <div
                            key={item.id}
                            className={`history-item ${item.id === activeId ? 'active' : ''}`}
                            onClick={() => onSelect(item.id)}
                        >
                            <span className="history-icon">📄</span>
                            <div className="history-text">
                                <div className="history-query">{item.query}</div>
                                <div className="history-date">{formatDate(item.created_at)}</div>
                            </div>
                            <span className={`history-status ${item.status || 'completed'}`} />
                        </div>
                    ))
                )}
            </div>

            {/* User Profile Section */}
            {userEmail && (
                <div className="sidebar-user">
                    <div className="user-email" title={userEmail}>
                        {userEmail}
                    </div>
                    <button className="logout-btn" onClick={onLogout} title="Log out">
                        Logout
                    </button>
                </div>
            )}
        </aside>
    )
}

export default HistorySidebar
