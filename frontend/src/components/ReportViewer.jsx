/**
 * ReportViewer.jsx — Research Report Display
 * ============================================
 * WHY THIS COMPONENT:
 * After all 4 agents complete, the final Markdown report is displayed here.
 * We use react-markdown to render the Markdown into beautiful HTML that
 * matches our GenZ design system.
 *
 * Features:
 * 1. Full Markdown rendering (headers, lists, bold, links, code blocks, etc.)
 * 2. Glassmorphic card container — consistent with the rest of the UI
 * 3. Copy button — one click to copy the full report text
 * 4. "New Research" button — starts a fresh research session
 * 5. GFM support — GitHub Flavored Markdown (tables, strikethrough, etc.)
 *
 * WHY react-markdown (not dangerouslySetInnerHTML):
 * react-markdown safely converts Markdown to React components.
 * dangerouslySetInnerHTML would require a separate Markdown→HTML library
 * AND expose us to XSS attacks if the LLM output contains malicious HTML.
 */

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import ChartVisualizations from './ChartVisualizations'

function ReportViewer({ report, query, onNewResearch, onCopy, chartData = null }) {

    const handleExportPDF = async () => {
        const element = document.getElementById('report-content-export');
        if (!element) return;

        // Add a class temporarily to force light mode for the PDF
        element.classList.add('pdf-mode');

        try {
            // Wait a small tick for CSS to apply
            await new Promise(resolve => setTimeout(resolve, 300));

            const canvas = await html2canvas(element, {
                scale: 1, // Reduced to 1 to prevent huge canvas failure
                useCORS: true,
                backgroundColor: '#ffffff',
                logging: false, // Turn off logging
                allowTaint: true
            });

            if (canvas.width === 0 || canvas.height === 0) {
                console.error("Canvas is empty.");
                return;
            }

            const imgData = canvas.toDataURL('image/jpeg', 0.95);
            if (imgData === 'data:,') {
                console.error("Canvas export failed (corrupt data URI).");
                return;
            }

            // Create PDF (letter size: 8.5 x 11 inches)
            const pdf = new jsPDF({
                orientation: 'portrait',
                unit: 'in',
                format: 'letter'
            });

            const pageHeight = pdf.internal.pageSize.getHeight();
            const pageWidth = pdf.internal.pageSize.getWidth();
            const margin = 0.5;

            const pdfImgWidth = pageWidth - (margin * 2);
            const pdfImgHeight = (canvas.height * pdfImgWidth) / canvas.width;

            let heightLeft = pdfImgHeight;
            let position = margin;

            // First page
            pdf.addImage(imgData, 'JPEG', margin, position, pdfImgWidth, pdfImgHeight);
            heightLeft -= (pageHeight - margin * 2);

            // Additional pages if needed
            while (heightLeft > 0) {
                position -= (pageHeight - margin * 2);
                pdf.addPage();
                pdf.addImage(imgData, 'JPEG', margin, position, pdfImgWidth, pdfImgHeight);
                heightLeft -= (pageHeight - margin * 2);
            }

            const filename = typeof query === 'string' && query.trim() !== ''
                ? `${query.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_report.pdf`
                : 'research_report.pdf';

            pdf.save(filename);

        } catch (error) {
            console.error("PDF Export failed:", error);
            alert("Sorry, an error occurred while exporting the PDF.");
        } finally {
            // Remove the light mode class after export
            element.classList.remove('pdf-mode');
        }
    };

    // Custom renderers
    const components = {
        // Look for text like [1] and style it
        text: (props) => {
            // react-markdown doesn't easily let us override text nodes directly this way in newer versions without rehype,
            // so we'll just rely on CSS and standard formatting.
            return props.children;
        },
        a: ({ node, ...props }) => {
            // Find citation links if LLM generated them
            if (props.children && typeof props.children[0] === 'string' && props.children[0].match(/^\[\d+\]$/)) {
                return <sup className="citation-sup"><a {...props}>{props.children}</a></sup>
            }
            return <a {...props} />
        }
    }

    return (
        <div className="report-container">
            {/* Header with actions */}
            <div className="report-header">
                <div>
                    <h2>Research Report</h2>
                    <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '4px' }}>
                        Query: "{query}"
                    </p>
                </div>

                <div className="report-actions">
                    <button
                        className="report-action-btn"
                        onClick={handleExportPDF}
                        id="export-pdf-btn"
                    >
                        📥 Export PDF
                    </button>
                    <button
                        className="report-action-btn"
                        onClick={onCopy}
                        id="copy-report-btn"
                    >
                        📋 Copy
                    </button>
                    <button
                        className="report-action-btn"
                        onClick={onNewResearch}
                        id="new-research-btn"
                    >
                        ✨ New Research
                    </button>
                </div>
            </div>

            {/* Report content */}
            <div className="report-card" id="report-content-export">
                <div className="markdown-body">
                    {report ? (
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={components}
                        >
                            {report}
                        </ReactMarkdown>
                    ) : (
                        <p style={{ color: 'var(--text-muted)', textAlign: 'center' }}>
                            No report content available.
                        </p>
                    )}
                </div>
                {chartData && <ChartVisualizations data={chartData} />}
            </div>
        </div>
    )
}

export default ReportViewer
