interface Props { score: number; size?: number; label?: string }

export default function ScoreRing({ score, size = 120, label = 'Overall' }: Props) {
  const r = 44
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  const color = score >= 80 ? '#10b981' : score >= 60 ? '#3b82f6' : score >= 40 ? '#f59e0b' : '#ef4444'

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#e2e8f0" strokeWidth="8" />
        <circle cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round" transform="rotate(-90 50 50)" style={{ transition: 'stroke-dashoffset 1s ease' }} />
        <text x="50" y="46" textAnchor="middle" fontSize="18" fontWeight="bold" fill={color}>{score}</text>
        <text x="50" y="60" textAnchor="middle" fontSize="9" fill="#94a3b8">/100</text>
      </svg>
      <span className="text-xs font-medium text-slate-500">{label}</span>
    </div>
  )
}
