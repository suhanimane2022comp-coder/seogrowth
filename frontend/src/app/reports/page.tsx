'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { getProjects } from '@/lib/api'
import ScoreRing from '@/components/ScoreRing'
import StatusBadge from '@/components/StatusBadge'
import { FileText, ExternalLink, PlusCircle } from 'lucide-react'

interface Project {
  id: number; business_name: string; status: string
  target_location: string; created_at: string; overall_score?: number
}

export default function ReportsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getProjects().then(({ data }) => setProjects(data)).finally(() => setLoading(false))
  }, [])

  const completed = projects.filter(p => p.status === 'completed')

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">SEO Reports</h1>
          <p className="text-slate-500 text-sm mt-0.5">{completed.length} completed {completed.length === 1 ? 'report' : 'reports'}</p>
        </div>
        <Link href="/analyze" className="btn-primary flex items-center gap-2">
          <PlusCircle className="w-4 h-4" /> New Analysis
        </Link>
      </div>

      {loading ? (
        <div className="card text-center py-12 text-slate-400">Loading reports…</div>
      ) : completed.length === 0 ? (
        <div className="card text-center py-16">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="font-semibold text-slate-600 mb-2">No completed reports yet</h3>
          <p className="text-slate-400 text-sm mb-6">Run an analysis to generate your first SEO report</p>
          <Link href="/analyze" className="btn-primary inline-flex items-center gap-2">
            <PlusCircle className="w-4 h-4" /> Start Analysis
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {completed.map(p => (
            <div key={p.id} className="card flex items-center gap-6 hover:shadow-md transition">
              <ScoreRing score={p.overall_score ?? 0} size={80} />
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-bold text-slate-800 text-lg">{p.business_name}</h3>
                  <StatusBadge status={p.status} />
                </div>
                <p className="text-sm text-slate-500">📍 {p.target_location} · 📅 {new Date(p.created_at).toLocaleDateString()}</p>
              </div>
              <Link href={`/reports/${p.id}`}
                className="btn-primary flex items-center gap-2 text-sm">
                <ExternalLink className="w-4 h-4" /> View Report
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
