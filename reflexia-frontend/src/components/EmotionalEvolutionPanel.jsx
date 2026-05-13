import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend)

const palette = ['#2f6e58', '#7f6721', '#a03939', '#2f7e7a', '#53675f']

function formatDate(value) {
  try {
    return new Intl.DateTimeFormat('ca-ES', {
      day: '2-digit',
      month: 'short',
    }).format(new Date(value))
  } catch {
    return value
  }
}

function buildChartData(evolution) {
  const labels = evolution.data_points.map((point) => formatDate(point.date))
  const emotions = evolution.frequent_emotions.map((item) => item.emotion)

  return {
    labels,
    datasets: emotions.map((emotion, index) => ({
      label: emotion,
      data: evolution.data_points.map((point) => point.emotions[emotion] || 0),
      backgroundColor: palette[index % palette.length] + 'cc',
      borderColor: palette[index % palette.length],
      borderWidth: 1,
    })),
  }
}

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  scales: {
    x: {
      stacked: true,
      grid: { display: false },
    },
    y: {
      stacked: true,
      ticks: {
        callback: (value) => `${value}%`,
      },
    },
  },
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        usePointStyle: true,
        pointStyle: 'rect',
        boxWidth: 10,
      },
      onClick: (e, legendItem, legend) => {
        const index = legendItem.datasetIndex
        const ci = legend.chart
        const isIsolated = ci.data.datasets.every((_, i) =>
          i === index ? ci.isDatasetVisible(i) : !ci.isDatasetVisible(i)
        )
        if (isIsolated) {
          ci.data.datasets.forEach((_, i) => ci.show(i))
        } else {
          ci.data.datasets.forEach((_, i) => {
            if (i === index) ci.show(i)
            else ci.hide(i)
          })
        }
      },
    },
    tooltip: {
      callbacks: {
        label: (context) => `${context.dataset.label}: ${context.parsed.y}%`,
      },
    },
  },
}

export function EmotionalEvolutionPanel({ evolution, isLoading = false }) {
  if (isLoading) {
    return <p className="muted">Carregant evolucio emocional...</p>
  }

  if (!evolution || !evolution.has_enough_data) {
    return (
      <div className="content-card section-stack entries-summary-card">
        <h3>Encara no hi ha prou informació</h3>
        <p className="muted">
          {evolution?.message || 'Calen almenys dues entrades analitzades per construir el grafic d’evolucio emocional.'}
        </p>
      </div>
    )
  }

  const chartData = buildChartData(evolution)
  const topEmotion = evolution.frequent_emotions.reduce(
    (best, item) => (item.average_percentage > best.average_percentage ? item : best),
    evolution.frequent_emotions[0]
  )

  return (
    <div className="section-stack">
      <div className="stat-list">
        <div className="stat-card">
          <span>Entrades analitzades</span>
          <strong>{evolution.analyzed_entries_count}</strong>
        </div>
        <div className="stat-card">
          <span>Emoció principal</span>
          <strong>{topEmotion?.emotion || 'Sense dades'}</strong>
        </div>
        <div className="stat-card">
          <span>Risc alt</span>
          <strong>{evolution.risk_counts.high || 0}</strong>
        </div>
      </div>

      <div className="analysis-chart-panel">
        <Bar data={chartData} options={chartOptions} />
      </div>

      <div className="analysis-inline-list">
        {evolution.frequent_emotions.map((item) => (
          <span className="status-pill" key={item.emotion}>
            {item.emotion}: {Math.round(item.average_percentage)}%
          </span>
        ))}
      </div>
    </div>
  )
}
