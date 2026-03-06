import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
);

function ChartVisualizations({ data }) {
    if (!data || !Array.isArray(data) || data.length === 0) {
        return null;
    }

    // Deduplicate and sanitize data
    const safeData = data.filter(item => item && item.label && typeof item.value === 'number');

    if (safeData.length === 0) return null;

    const labels = safeData.map(d => d.label);
    const values = safeData.map(d => d.value);

    const colors = [
        'rgba(168, 85, 247, 0.8)', // Purple
        'rgba(236, 72, 153, 0.8)', // Pink
        'rgba(6, 182, 212, 0.8)',  // Cyan
        'rgba(34, 197, 94, 0.8)',  // Green
        'rgba(234, 179, 8, 0.8)',  // Yellow
        'rgba(239, 68, 68, 0.8)'   // Red
    ];

    const chartData = {
        labels,
        datasets: [
            {
                label: 'Extracted Data',
                data: values,
                backgroundColor: colors.slice(0, values.length),
                borderColor: colors.slice(0, values.length).map(c => c.replace('0.8', '1')),
                borderWidth: 1,
            },
        ],
    };

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
                labels: { color: '#f0eef6' }
            },
            title: {
                display: true,
                text: 'Key Metrics Analysis',
                color: '#f0eef6',
                font: { size: 16 }
            },
        },
        scales: {
            y: {
                ticks: { color: '#a09bb5' },
                grid: { color: 'rgba(255, 255, 255, 0.1)' }
            },
            x: {
                ticks: { color: '#a09bb5' },
                grid: { color: 'rgba(255, 255, 255, 0.1)' }
            }
        }
    };

    const donutOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: 'right',
                labels: { color: '#f0eef6' }
            }
        }
    };

    return (
        <div className="chart-section" style={{ marginTop: '40px', padding: '20px', background: 'rgba(0,0,0,0.2)', borderRadius: '12px' }}>
            <h3 style={{ color: 'var(--accent-purple)', marginBottom: '20px' }}>Data Visualizations</h3>
            <div style={{ display: 'flex', gap: '30px', flexWrap: 'wrap' }}>
                <div style={{ flex: '1 1 400px', minWidth: '300px' }}>
                    <Bar options={options} data={chartData} />
                </div>
                {safeData.length <= 6 && safeData.length > 1 && (
                    <div style={{ flex: '0 1 300px', margin: '0 auto' }}>
                        <Doughnut options={donutOptions} data={chartData} />
                    </div>
                )}
            </div>
        </div>
    );
}

export default ChartVisualizations;
