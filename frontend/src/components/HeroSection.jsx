/**
 * HeroSection.jsx — Landing Hero Component
 * ==========================================
 * WHY THIS COMPONENT:
 * First impressions matter. The hero section is what the user sees
 * immediately when they open the app. It needs to:
 * 1. Communicate what the app does (research assistant)
 * 2. Feel exciting and modern (GenZ vibe)
 * 3. Draw the eye downward to the input form
 *
 * Design choices:
 * - "Research, but make it ✨ smart" — GenZ-style casual tone
 * - Gradient text on the key word — draws attention
 * - Badge with "Powered by AI" — establishes credibility
 * - Subtitle explaining the 4-agent system — sets expectations
 */

function HeroSection() {
    return (
        <section className="hero" id="hero-section">
            {/* Badge — adds a premium, branded feel */}
            <div className="hero-badge">
                <span>⚡</span>
                <span>Powered by 4 AI Agents</span>
            </div>

            {/* Main heading — gradient text on key phrase */}
            <h1>
                Research, but make it{' '}
                <span className="gradient-text">✨ smart</span>
            </h1>

            {/* Subtitle — explains what the app does */}
            <p>
                Drop your research question and let our AI squad handle the rest.
                Four specialized agents plan, search, analyze, and write a
                comprehensive report — all in real time.
            </p>
        </section>
    )
}

export default HeroSection
