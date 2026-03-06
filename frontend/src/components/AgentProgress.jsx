/**
 * AgentProgress.jsx — Agent Pipeline Visualization
 * ==================================================
 * WHY THIS COMPONENT:
 * This is the STAR of the UI. While agents work, users see a real-time
 * visualization of the pipeline:
 *
 *   🧠 Planner ──── ✅ Done
 *       │
 *   🔍 Search ──── ⏳ Active (pulsing glow)
 *       │
 *   📊 Analyzer ── ⏸ Waiting
 *       │
 *   ✍️  Writer ──── ⏸ Waiting
 *
 * WHY a pipeline (not a progress bar):
 * A progress bar shows "40% done" — meaningless. The pipeline shows:
 * - WHICH agent is working right now
 * - WHAT each agent does (via role descriptions)
 * - HOW MANY steps are left
 * This makes the wait educational and engaging rather than frustrating.
 *
 * States for each agent:
 * - 'waiting': greyed out, hasn't started yet
 * - 'active': purple glow, pulsing animation, showing status text
 * - 'done': green, checkmark, completed
 *
 * WHY real-time updates:
 * These come from SSE events. The parent App component updates the
 * agentStates object, and React re-renders only the changed agents.
 */

const AGENTS = [
    {
        key: 'planner',
        icon: '🧠',
        name: 'Planner Agent',
        role: 'Breaks down your question into focused research sub-tasks',
    },
    {
        key: 'search',
        icon: '🔍',
        name: 'Search Agent',
        role: 'Searches the web for relevant sources and articles',
    },
    {
        key: 'analyzer',
        icon: '📊',
        name: 'Analyzer Agent',
        role: 'Extracts insights and identifies patterns across sources',
    },
    {
        key: 'writer',
        icon: '✍️',
        name: 'Writer Agent',
        role: 'Compiles everything into a polished research report',
    },
]

function AgentProgress({ query, agentStates }) {
    return (
        <div className="progress-container">
            <h2 className="progress-title">Agents at Work</h2>
            <p className="progress-subtitle">
                Researching: <strong>"{query}"</strong>
            </p>

            <div className="pipeline">
                {AGENTS.map((agent) => {
                    const state = agentStates[agent.key] || { status: 'waiting', message: '' }

                    return (
                        <div
                            key={agent.key}
                            className={`pipeline-agent ${state.status}`}
                            id={`agent-${agent.key}`}
                        >
                            {/* Agent Icon Node */}
                            <div className="agent-node">
                                {state.status === 'done' ? '✅' : agent.icon}
                            </div>

                            {/* Agent Info */}
                            <div className="agent-info">
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                                    <div className="agent-name">{agent.name}</div>
                                    <span className="agent-status-badge">
                                        {state.status === 'active' && (
                                            <span className="spinner" />
                                        )}
                                        {state.status === 'waiting' && 'Waiting'}
                                        {state.status === 'active' && 'Running'}
                                        {state.status === 'done' && 'Complete'}
                                    </span>
                                </div>

                                <div className="agent-role">{agent.role}</div>

                                {/* Status message — only shown for active and done agents */}
                                {(state.status === 'active' || state.status === 'done') && state.message && (
                                    <div className="agent-status-text">
                                        {state.message.length > 200
                                            ? state.message.substring(0, 200) + '...'
                                            : state.message
                                        }
                                    </div>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

export default AgentProgress
