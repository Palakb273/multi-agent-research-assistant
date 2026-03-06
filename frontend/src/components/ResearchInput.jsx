/**
 * ResearchInput.jsx — Research Query Input Component
 * ====================================================
 * WHY THIS COMPONENT:
 * This is the primary interaction point. The user types their research
 * question here and hits "Generate Report". Design goals:
 * 1. Glassmorphic card (frosted glass effect) — premium feel
 * 2. Glowing border on focus — visual feedback that it's active
 * 3. Topic chips below — inspiration for users who don't know what to ask
 * 4. Character count — gives feedback without being restrictive
 * 5. Big, attractive submit button — clear call-to-action
 *
 * WHY topic chips:
 * Users often have "blank page syndrome" — they don't know what to type.
 * Pre-made chips give them instant starting points. Clicking a chip
 * fills the textarea automatically.
 */

import { useState } from 'react'

const SUGGESTED_TOPICS = [
    'AI Ethics & Bias in 2025',
    'Quantum Computing Breakthroughs',
    'Climate Change Solutions',
    'Future of Remote Work',
    'Web3 & Blockchain Evolution',
    'Mental Health & Gen Z',
]

function ResearchInput({ onSubmit, error }) {
    const [inputValue, setInputValue] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)

    const handleSubmit = async () => {
        const trimmed = inputValue.trim()
        if (!trimmed || isSubmitting) return

        setIsSubmitting(true)
        await onSubmit(trimmed)
        setIsSubmitting(false)
    }

    const handleKeyDown = (e) => {
        // WHY Ctrl+Enter instead of Enter:
        // Enter creates newlines (expected in a textarea).
        // Ctrl+Enter is the universal "submit" shortcut for text areas.
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault()
            handleSubmit()
        }
    }

    const handleChipClick = (topic) => {
        setInputValue(topic)
    }

    return (
        <>
            <div className="research-input-container">
                <div className="research-input-card" id="research-input">
                    <textarea
                        className="research-textarea"
                        placeholder="What do you want to research? Try something like 'Impact of AI on healthcare systems' or 'Latest breakthroughs in renewable energy'..."
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        id="research-query-textarea"
                    />

                    <div className="research-input-footer">
                        <span className="char-count">
                            {inputValue.length} characters • Ctrl+Enter to submit
                        </span>

                        <button
                            className="submit-btn"
                            onClick={handleSubmit}
                            disabled={!inputValue.trim() || isSubmitting}
                            id="submit-research-btn"
                        >
                            {isSubmitting ? (
                                <>
                                    <span className="spinner" />
                                    Generating...
                                </>
                            ) : (
                                <>
                                    Generate Report 🚀
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Error display */}
                {error && (
                    <div className="error-container" style={{ margin: '20px 0', padding: '20px' }}>
                        <div className="error-icon">⚠️</div>
                        <div className="error-title">Something went wrong</div>
                        <div className="error-message">{error}</div>
                    </div>
                )}
            </div>

            {/* Suggested topic chips */}
            <div className="topic-chips">
                {SUGGESTED_TOPICS.map((topic) => (
                    <button
                        key={topic}
                        className="topic-chip"
                        onClick={() => handleChipClick(topic)}
                    >
                        {topic}
                    </button>
                ))}
            </div>
        </>
    )
}

export default ResearchInput
