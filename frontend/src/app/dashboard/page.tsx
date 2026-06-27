'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { getProjects, deleteProject, getProfile, getAudience, getCompetitors, getReport, getAgentAnalytics } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import ScoreRing from '@/components/ScoreRing'
import StatusBadge from '@/components/StatusBadge'
import {
  PlusCircle, Trash2, ExternalLink, TrendingUp, AlertTriangle, Search, FileText,
  Building2, Users, Swords, Bot, ExternalLinkIcon,
} from 'lucide-react'

interface Project {
  id: number; business_name: string; status: string
  website_url?: string; target_location: string; created_at: string
  overall_score?: number; pages_crawled?: number
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  const [profile, setProfile] = useState<any>(null)
  const [audience, setAudience] = useState<any>(null)
  const [competitors, setCompetitors] = useState<any[]>([])
  const [agents, setAgents] = useState<any[]>([])
  const [latestReport, setLatestReport] = useState<any>(null)

  const fetchProjects = async () => {
    try {
      const { data } = await getProjects()
      setProjects(data)
    } catch {}
    setLoading(false)
  }

  const fetchExtras = async () => {
    try { setProfile((await getProfile()).data) } catch {}
    try { setAudience((await getAudience()).data) } catch {}
    try { setCompetitors((await getCompetitors()).data) } catch {}
    try { setAgents((await getAgentAnalytics()).data) } catch {}
  }

  useEffect(() => { fetchProjects(); fetchExtras() }, [])

  useEffect(() => {
    const completedProjects = projects.filter(p => p.status === 'completed')
    if (completedProjects.length === 0) return
    const latest = completedProjects[0]
    getReport(latest.id).then(({ data }) => setLatestReport({ ...data, business_name: latest.business_name })).catch(() => {})
  }, [projects])

  // Auto-refresh if any projects are running
  useEffect(() => {
    const hasRunning = projects.some(p => p.status === 'running' || p.status === 'pending')
    if (!hasRunning) return
    const timer = setInterval(() => { fetchProjects(); fetchExtras() }, 5000)
    return () => clearInterval(timer)
  }, [projects])

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this project?')) return
    await deleteProject(id)
    setProjects(p => p.filter(x => x.id !== id))
  }

  const completed = projects.filter(p => p.status === 'completed')
  const avgScore = completed.length ? Math.round(completed.reduce((a, p) => a + (p.overall_score ?? 0), 0) / completed.length) : 0

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
          <p className="text-slate-500 text-sm mt-0.5">Welcome back, {user?.name}</p>
        </div>
        <Link href="/analyze" className="btn-primary flex items-center gap-2">
          <PlusCircle className="w-4 h-4" /> New Analysis
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Total Projects', value: projects.length, Icon: FileText, color: 'text-brand-600' },
          { label: 'Completed', value: completed.length, Icon: TrendingUp, color: 'text-emerald-600' },
          { label: 'Avg SEO Score', value: avgScore ? `${avgScore}/100` : '—', Icon: Search, color: 'text-blue-600' },
          { label: 'Running', value: projects.filter(p => p.status === 'running').length, Icon: AlertTriangle, color: 'text-amber-600' },
        ].map(({ label, value, Icon, color }) => (
          <div key={label} className="card">
            <Icon className={`w-6 h-6 ${color} mb-3`} />
            <div className="text-2xl font-bold text-slate-800">{value}</div>
            <div className="text-xs text-slate-500 mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* Profile / Audience / Competitor / Latest Report Cards */}
      <div className="grid md:grid-cols-2 gap-4 mb-8">
        {/* Profile Summary */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Building2 className="w-5 h-5 text-brand-600" />
            <h3 className="font-semibold text-slate-700">Profile Summary</h3>
            <Link href="/profile/setup" className="ml-auto text-xs text-brand-600 hover:underline">Edit</Link>
          </div>
          {profile ? (
            <div className="space-y-1.5 text-sm text-slate-600">
              <p><span className="text-slate-400">Business:</span> {profile.business_name}</p>
              <p><span className="text-slate-400">Industry:</span> {profile.industry}</p>
              {profile.website_url && <p><span className="text-slate-400">Website:</span> {profile.website_url}</p>}
              <p className="flex flex-wrap gap-1 mt-2">
                {(profile.keywords || []).slice(0, 6).map((k: string) => (
                  <span key={k} className="badge-info">{k}</span>
                ))}
              </p>
            </div>
          ) : <p className="text-slate-400 text-sm">No profile yet.</p>}
        </div>

        {/* Target Audience */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-5 h-5 text-brand-600" />
            <h3 className="font-semibold text-slate-700">Target Audience</h3>
          </div>
          {audience ? (
            <div className="space-y-1.5 text-sm text-slate-600">
              <p><span className="text-slate-400">Age Group:</span> {audience.age_group}</p>
              <p className="flex flex-wrap gap-1"><span className="text-slate-400">Interests:</span>
                {(audience.interests || []).slice(0, 4).map((i: string) => <span key={i} className="badge-success ml-1">{i}</span>)}
              </p>
              <p className="flex flex-wrap gap-1"><span className="text-slate-400">Pain points:</span>
                {(audience.pain_points || []).slice(0, 3).map((i: string) => <span key={i} className="badge-warning ml-1">{i}</span>)}
              </p>
              <p className="flex flex-wrap gap-1"><span className="text-slate-400">Platforms:</span>
                {(audience.preferred_platforms || []).map((i: string) => <span key={i} className="badge-info ml-1">{i}</span>)}
              </p>
            </div>
          ) : <p className="text-slate-400 text-sm">No audience persona yet.</p>}
        </div>

        {/* Competitors */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Swords className="w-5 h-5 text-brand-600" />
            <h3 className="font-semibold text-slate-700">Competitors</h3>
          </div>
          {competitors.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 text-left">
                  <th className="font-medium pb-2">Competitor</th>
                  <th className="font-medium pb-2">Website</th>
                  <th className="font-medium pb-2">Category</th>
                </tr>
              </thead>
              <tbody>
                {competitors.slice(0, 5).map((c) => (
                  <tr key={c.id} className="border-t border-slate-100">
                    <td className="py-2 font-medium text-slate-700">{c.name}</td>
                    <td className="py-2">
                      {c.website_url && (
                        <a href={c.website_url} target="_blank" rel="noreferrer" className="text-brand-600 hover:underline flex items-center gap-1">
                          Visit <ExternalLinkIcon className="w-3 h-3" />
                        </a>
                      )}
                    </td>
                    <td className="py-2 text-slate-500">{c.category}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="text-slate-400 text-sm">No competitors detected yet.</p>}
        </div>

        {/* Latest SEO Report */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <FileText className="w-5 h-5 text-brand-600" />
            <h3 className="font-semibold text-slate-700">Latest SEO Report</h3>
          </div>
          {latestReport ? (
            <div className="flex items-center gap-4">
              <ScoreRing score={latestReport.overall_score ?? 0} size={64} />
              <div className="text-sm text-slate-600 space-y-1">
                <p className="font-medium text-slate-700">{latestReport.business_name}</p>
                <p>Technical: {latestReport.report_data?.technical_score ?? '—'} | Content: {latestReport.report_data?.content_score ?? '—'} | Backlink: {latestReport.report_data?.backlink_score ?? '—'}</p>
                <Link href="/reports" className="text-brand-600 text-xs hover:underline">View all recommendations →</Link>
              </div>
            </div>
          ) : <p className="text-slate-400 text-sm">No completed reports yet.</p>}
        </div>
      </div>

      {/* Agent Progress */}
      <div className="card mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Bot className="w-5 h-5 text-brand-600" />
          <h3 className="font-semibold text-slate-700">Agent Progress</h3>
        </div>
        {agents.length > 0 ? (
          <div className="grid md:grid-cols-2 gap-4">
            {agents.map((a) => (
              <div key={a.agent_name} className="border border-slate-100 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-slate-700 text-sm">{a.agent_name}</span>
                  <StatusBadge status={a.status} />
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 mb-2">
                  <div className="bg-brand-600 h-2 rounded-full transition-all" style={{ width: `${a.progress_pct}%` }} />
                </div>
                <div className="flex justify-between text-xs text-slate-400">
                  <span>{a.completed_tasks} tasks completed</span>
                  <span>{new Date(a.last_execution).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        ) : <p className="text-slate-400 text-sm">Agents will appear here once you set up your profile.</p>}
      </div>

      {/* Projects list */}
      <h2 className="font-semibold text-slate-700 mb-4">Your Projects</h2>

      {loading ? (
        <div className="card text-center py-12 text-slate-400">Loading projects…</div>
      ) : projects.length === 0 ? (
        <div className="card text-center py-16">
          <Search className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="font-semibold text-slate-600 mb-2">No analyses yet</h3>
          <p className="text-slate-400 text-sm mb-6">Create your first SEO analysis to get started</p>
          <Link href="/analyze" className="btn-primary inline-flex items-center gap-2">
            <PlusCircle className="w-4 h-4" /> Start Analysis
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {projects.map(project => (
            <div key={project.id} className="card flex items-center gap-6 hover:shadow-md transition">
              {project.status === 'completed' && project.overall_score != null ? (
                <ScoreRing score={project.overall_score} size={80} />
              ) : (
                <div className="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center flex-shrink-0">
                  <Search className="w-7 h-7 text-slate-300" />
                </div>
              )}

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-bold text-slate-800 text-lg">{project.business_name}</h3>
                  <StatusBadge status={project.status} />
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-500">
                  {project.website_url && <span>🌐 {project.website_url}</span>}
                  <span>📍 {project.target_location}</span>
                  {project.pages_crawled != null && project.pages_crawled > 0 && (
                    <span>📄 {project.pages_crawled} pages</span>
                  )}
                  <span>🕒 {new Date(project.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 flex-shrink-0">
                {project.status === 'completed' && (
                  <Link href={`/reports/${project.id}`}
                    className="btn-secondary flex items-center gap-2 text-sm py-2">
                    <ExternalLink className="w-4 h-4" /> Report
                  </Link>
                )}
                <button onClick={() => handleDelete(project.id)}
                  className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
