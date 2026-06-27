'use client'
import { useEffect, useState } from 'react'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { getSeoAnalytics, getCompetitorAnalytics, getAudienceAnalytics, getSocialAnalytics, getAgentAnalytics } from '@/lib/api'
import { Loader2 } from 'lucide-react'

const COLORS = ['#4f46e5', '#06b6d4', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899']

export default function AnalyticsPage() {
  const [seo, setSeo] = useState<any>(null)
  const [competitors, setCompetitors] = useState<any>(null)
  const [audience, setAudience] = useState<any>(null)
  const [social, setSocial] = useState<any>(null)
  const [agents, setAgents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getSeoAnalytics().then((r) => setSeo(r.data)).catch(() => {}),
      getCompetitorAnalytics().then((r) => setCompetitors(r.data)).catch(() => {}),
      getAudienceAnalytics().then((r) => setAudience(r.data)).catch(() => {}),
      getSocialAnalytics().then((r) => setSocial(r.data)).catch(() => {}),
      getAgentAnalytics().then((r) => setAgents(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-brand-600" /></div>
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Analytics Dashboard</h1>
        <p className="text-slate-500 text-sm mt-1">A full view of your SEO, competitor, audience, social, and agent performance.</p>
      </div>

      {/* SEO Analytics */}
      <section>
        <h2 className="font-semibold text-slate-700 mb-3">SEO Analytics</h2>
        <div className="card">
          {seo?.trend?.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={seo.trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} domain={[0, 100]} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="seo_score" name="SEO Score" stroke="#4f46e5" strokeWidth={2} />
                <Line type="monotone" dataKey="technical_score" name="Technical SEO" stroke="#06b6d4" strokeWidth={2} />
                <Line type="monotone" dataKey="content_score" name="Content Score" stroke="#f59e0b" strokeWidth={2} />
                <Line type="monotone" dataKey="keyword_score" name="Keyword Ranking" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : <EmptyState text="Run an SEO analysis to see trends here." />}
        </div>
      </section>

      {/* Competitor Analytics */}
      <section>
        <h2 className="font-semibold text-slate-700 mb-3">Competitor Analytics</h2>
        <div className="card">
          {competitors?.competitors?.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={competitors.competitors}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 12 }} domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="domain_authority_score" name="Estimated Domain Authority / Visibility" fill="#4f46e5" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState text="No competitor data yet." />}
        </div>
      </section>

      {/* Audience Analytics */}
      <section>
        <h2 className="font-semibold text-slate-700 mb-3">Audience Analytics</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="card">
            <h3 className="text-sm font-medium text-slate-500 mb-2">Gender Distribution</h3>
            {audience?.gender?.length ? (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie data={audience.gender} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                    {audience.gender.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip /><Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : <EmptyState text="No audience data yet." />}
          </div>
          <div className="card">
            <h3 className="text-sm font-medium text-slate-500 mb-2">Age Distribution</h3>
            {audience?.age_group ? (
              <div className="flex items-center justify-center h-[240px]">
                <div className="text-center">
                  <div className="text-4xl font-bold text-brand-600">{audience.age_group}</div>
                  <p className="text-slate-400 text-sm mt-2">Primary target age group</p>
                </div>
              </div>
            ) : <EmptyState text="No age data yet." />}
          </div>
        </div>
      </section>

      {/* Social Media Analytics */}
      <section>
        <h2 className="font-semibold text-slate-700 mb-3">Social Media Analytics</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="card">
            <h3 className="text-sm font-medium text-slate-500 mb-2">Posts Published &amp; Engagement Growth</h3>
            {social?.posts_published?.length ? (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={social.posts_published}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="published" name="Posts Published" fill="#4f46e5" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="engagement" name="Engagement Score" fill="#10b981" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <EmptyState text="Generate a social calendar to see analytics here." />}
          </div>
          <div className="card">
            <h3 className="text-sm font-medium text-slate-500 mb-2">Platform Distribution (Reach)</h3>
            {social?.platform_distribution?.length ? (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie data={social.platform_distribution} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                    {social.platform_distribution.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip /><Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : <EmptyState text="No platform data yet." />}
          </div>
        </div>
      </section>

      {/* Agent Analytics */}
      <section>
        <h2 className="font-semibold text-slate-700 mb-3">Agent Analytics</h2>
        <div className="card">
          {agents.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={agents}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="agent_name" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" height={70} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="completed_tasks" name="Tasks Completed" fill="#4f46e5" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState text="No agent activity yet." />}
        </div>
      </section>
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return <div className="flex items-center justify-center h-[200px] text-slate-400 text-sm">{text}</div>
}
