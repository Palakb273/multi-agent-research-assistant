/**
 * App.jsx — Main Application Component
 * ======================================
 * WHY THIS ARCHITECTURE:
 * The App manages the overall application state and layout.
 * It uses a simple state machine pattern (screen: 'input' | 'progress' | 'report')
 * instead of a router because we only have 3 views and they flow linearly.
 *
 * State Flow:
 *   'input' → user types query → 'progress' → agents run → 'report'
 *       ↑                                                       |
 *       └───── user clicks "New Research" ──────────────────────┘
 */

import { useState, useEffect, useCallback } from 'react'
import HeroSection from './components/HeroSection'
import ResearchInput from './components/ResearchInput'
import AgentProgress from './components/AgentProgress'
import ReportViewer from './components/ReportViewer'
import HistorySidebar from './components/HistorySidebar'
import AuthModal from './components/AuthModal'
import { supabase } from './lib/supabase'

// Back-end URL pointer (Uses environment variable in production, falls back to localhost)
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
    // ─── Auth State ───────────────────────────────────────
    const [session, setSession] = useState(null)
    const [authLoading, setAuthLoading] = useState(true)

    // ─── Application State ────────────────────────────────
    const [screen, setScreen] = useState('input')
    const [query, setQuery] = useState('')
    const [report, setReport] = useState('')
    const [chartData, setChartData] = useState(null)
    const [history, setHistory] = useState([])
    const [selectedTaskId, setSelectedTaskId] = useState(null)
    const [error, setError] = useState(null)
    const [copyToast, setCopyToast] = useState(false)

    const [agentStates, setAgentStates] = useState({
        planner: { status: 'waiting', message: '' },
        search: { status: 'waiting', message: '' },
        analyzer: { status: 'waiting', message: '' },
        writer: { status: 'waiting', message: '' },
    })

    // ─── Auth Initialization ──────────────────────────────
    useEffect(() => {
        // Get initial session
        supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session)
            setAuthLoading(false)
        })

        // Listen for auth changes (login, logout)
        const {
            data: { subscription },
        } = supabase.auth.onAuthStateChange((_event, session) => {
            setSession(session)
            // If user logs out, clear their data from screen
            if (!session) {
                setHistory([])
                setScreen('input')
                setReport('')
                setSelectedTaskId(null)
            }
        })

        return () => subscription.unsubscribe()
    }, [])

    // ─── Fetch History ────────────────────────────────────
    const fetchHistory = useCallback(async () => {
        // Don't fetch if not logged in
        if (!session) return;

        try {
            const res = await fetch(`${API_BASE}/api/history`, {
                headers: {
                    'Authorization': `Bearer ${session.access_token}`
                }
            })
            if (res.ok) {
                const data = await res.json()
                setHistory(data.history || [])
            }
        } catch (e) {
            console.log('History fetch failed:', e)
        }
    }, [session])

    // Fetch history whenever the session changes (e.g. user logs in)
    useEffect(() => {
        if (session) {
            fetchHistory()
        }
    }, [session, fetchHistory])

    // ─── Start Research ───────────────────────────────────
    const startResearch = async (researchQuery) => {
        if (!session) return;

        setQuery(researchQuery)
        setScreen('progress')
        setError(null)
        setReport('')
        setChartData(null)

        setAgentStates({
            planner: { status: 'waiting', message: '' },
            search: { status: 'waiting', message: '' },
            analyzer: { status: 'waiting', message: '' },
            writer: { status: 'waiting', message: '' },
        })

        try {
            const response = await fetch(`${API_BASE}/api/research`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${session.access_token}`
                },
                body: JSON.stringify({ query: researchQuery }),
            })

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`)
            }

            // Fetch history immediately so the user sees the 'in_progress' task in the sidebar
            fetchHistory()

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let buffer = ''

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')
                buffer = lines.pop() || ''

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const eventData = JSON.parse(line.slice(6))
                            handleSSEEvent(eventData)
                        } catch (e) {
                            // Skip malformed JSON lines
                        }
                    }
                }
            }
        } catch (e) {
            setError(e.message)
            setScreen('input')
        }
    }

    const handleSSEEvent = (event) => {
        const { agent, status, data, report: eventReport, chart_data: eventChartData, task_id } = event

        if (agent === 'complete' && status === 'done') {
            setReport(eventReport || '')
            setChartData(eventChartData || null)
            setSelectedTaskId(task_id)
            setScreen('report')
            fetchHistory()
            return
        }

        if (agent === 'error') {
            setError(data || 'An unknown error occurred')
            setScreen('input')
            return
        }

        setAgentStates(prev => ({
            ...prev,
            [agent]: { status, message: data || '' },
        }))
    }

    const loadHistoryItem = async (taskId) => {
        if (!session) return;

        try {
            const res = await fetch(`${API_BASE}/api/research/${taskId}`, {
                headers: {
                    'Authorization': `Bearer ${session.access_token}`
                }
            })
            if (res.ok) {
                const data = await res.json()
                setQuery(data.query || '')
                setReport(data.report || '')

                // Extract chartData from analysis text if it exists
                let extractedChartData = null;
                if (data.analysis) {
                    const match = data.analysis.match(/```json\s+([\s\S]*?)\s+```/);
                    if (match) {
                        try {
                            const parsed = JSON.parse(match[1]);
                            if (Array.isArray(parsed) && parsed.length > 0) {
                                extractedChartData = parsed;
                            }
                        } catch (err) {
                            console.log("Failed to parse chart data from history", err);
                        }
                    }
                }
                setChartData(extractedChartData);

                setSelectedTaskId(taskId)
                setScreen('report')
            }
        } catch (e) {
            console.error('Failed to load history item:', e)
        }
    }

    const startNew = () => {
        setScreen('input')
        setQuery('')
        setReport('')
        setChartData(null)
        setError(null)
        setSelectedTaskId(null)
    }

    const copyReport = () => {
        navigator.clipboard.writeText(report)
        setCopyToast(true)
        setTimeout(() => setCopyToast(false), 2000)
    }

    const handleLogout = async () => {
        await supabase.auth.signOut()
    }

    // ─── Render ───────────────────────────────────────────
    if (authLoading) {
        return <div className="app-container"><div className="spinner" style={{ margin: 'auto', width: '40px', height: '40px' }}></div></div>
    }

    // If not logged in, show Auth modal over a minimal background
    if (!session) {
        return (
            <div className="app-container">
                <div className="app-bg">
                    <div className="orb orb-1" />
                    <div className="orb orb-2" />
                    <div className="orb orb-3" />
                </div>
                <AuthModal />
            </div>
        )
    }

    return (
        <div className="app-container">
            <div className="app-bg">
                <div className="orb orb-1" />
                <div className="orb orb-2" />
                <div className="orb orb-3" />
            </div>

            <HistorySidebar
                history={history}
                activeId={selectedTaskId}
                onSelect={loadHistoryItem}
                onNewResearch={startNew}
                userEmail={session.user?.email}
                onLogout={handleLogout}
            />

            <main className="main-content">
                {screen === 'input' && (
                    <>
                        <HeroSection />
                        <ResearchInput
                            onSubmit={startResearch}
                            error={error}
                        />
                    </>
                )}

                {screen === 'progress' && (
                    <AgentProgress
                        query={query}
                        agentStates={agentStates}
                    />
                )}

                {screen === 'report' && (
                    <ReportViewer
                        report={report}
                        query={query}
                        chartData={chartData}
                        onNewResearch={startNew}
                        onCopy={copyReport}
                    />
                )}
            </main>

            {copyToast && (
                <div className="copy-toast">✓ Report copied to clipboard!</div>
            )}
        </div>
    )
}

export default App

