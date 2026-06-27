'use client'
import { useEffect, useState } from 'react'
import { generateSocialCalendar, listCalendars, getCalendarDetail, updatePostStatus } from '@/lib/api'
import { Loader2, Share2, Clock, TrendingUp, ChevronLeft, ChevronRight } from 'lucide-react'
import clsx from 'clsx'

const PLATFORMS = ['Instagram', 'Facebook', 'LinkedIn', 'Pinterest', 'X', 'YouTube', 'Threads']
const PAGE_SIZE = 10

export default function SocialPage() {
  const [selected, setSelected] = useState<string[]>(['Instagram', 'Facebook'])
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7))
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [calendars, setCalendars] = useState<any[]>([])
  const [detail, setDetail] = useState<any>(null)
  const [page, setPage] = useState(1)
  const [loadingDetail, setLoadingDetail] = useState(false)

  const fetchCalendars = async () => {
    try {
      const { data } = await listCalendars()
      setCalendars(data)
      if (data.length > 0) loadDetail(data[0].id)
    } catch {}
  }

  const loadDetail = async (id: number) => {
    setLoadingDetail(true)
    try {
      const { data } = await getCalendarDetail(id)
      setDetail(data)
      setPage(1)
    } catch {}
    setLoadingDetail(false)
  }

  useEffect(() => { fetchCalendars() }, [])

  const togglePlatform = (p: string) =>
    setSelected((prev) => (prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]))

  const handleGenerate = async () => {
    if (selected.length === 0) { setError('Select at least one platform'); return }
    setError('')
    setGenerating(true)
    try {
      const { data } = await generateSocialCalendar({ platforms: selected, month })
      setDetail(data)
      setPage(1)
      fetchCalendars()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate calendar')
    } finally {
      setGenerating(false)
    }
  }

  const handleStatusChange = async (postId: number, status: string) => {
    await updatePostStatus(postId, { status, actual_posted_date: status === 'Posted' ? new Date().toISOString().slice(0, 10) : null })
    if (detail) loadDetail(detail.id)
  }

  const posts = detail?.posts || []
  const totalPages = Math.max(1, Math.ceil(posts.length / PAGE_SIZE))
  const pagePosts = posts.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-800">Social Media Strategy Agent</h1>
        <p className="text-slate-500 text-sm mt-1">Pick your platforms and generate a monthly content calendar with prime posting times.</p>
      </div>

      {error && <div className="bg-red-50 text-red-600 text-sm rounded-xl px-4 py-3 mb-6">{error}</div>}

      {/* Platform selector */}
      <div className="card mb-6">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          {PLATFORMS.map((p) => (
            <button
              key={p}
              onClick={() => togglePlatform(p)}
              className={clsx(
                'px-4 py-2 rounded-xl text-sm font-medium border transition',
                selected.includes(p) ? 'bg-brand-600 text-white border-brand-600' : 'bg-white text-slate-600 border-slate-200 hover:border-brand-300'
              )}
            >
              {p}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <input type="month" className="input max-w-[160px]" value={month} onChange={(e) => setMonth(e.target.value)} />
          <button onClick={handleGenerate} disabled={generating} className="btn-primary flex items-center gap-2">
            {generating ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</> : <><Share2 className="w-4 h-4" /> Generate Calendar</>}
          </button>
          {calendars.length > 0 && (
            <select
              className="input max-w-[200px]"
              value={detail?.id || ''}
              onChange={(e) => loadDetail(Number(e.target.value))}
            >
              {calendars.map((c) => <option key={c.id} value={c.id}>{c.month}</option>)}
            </select>
          )}
        </div>
      </div>

      {loadingDetail ? (
        <div className="card text-center py-12 text-slate-400">Loading calendar...</div>
      ) : !detail ? (
        <div className="card text-center py-16">
          <Share2 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="font-semibold text-slate-600 mb-2">No calendar generated yet</h3>
          <p className="text-slate-400 text-sm">Pick your platforms above and generate your first monthly content calendar.</p>
        </div>
      ) : (
        <>
          <div className="grid md:grid-cols-3 gap-4 mb-6">
            {/* Platform priority */}
            <div className="card">
              <h3 className="font-semibold text-slate-700 mb-3 flex items-center gap-2"><TrendingUp className="w-4 h-4 text-brand-600" /> Platform Priority</h3>
              <div className="space-y-2">
                {(detail.platform_priority || []).map((p: any) => (
                  <div key={p.platform}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-slate-700">{p.platform}</span>
                      <span className="text-slate-400">{p.weight}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-1.5">
                      <div className="bg-brand-600 h-1.5 rounded-full" style={{ width: `${p.weight}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Engagement suggestions */}
            <div className="card">
              <h3 className="font-semibold text-slate-700 mb-3">Engagement Suggestions</h3>
              <div className="space-y-1.5">
                {(detail.engagement_suggestions || []).map((e: any) => (
                  <div key={e.type} className="flex justify-between text-sm">
                    <span className="text-slate-600">{e.type}</span>
                    <span className="badge-info">{e.priority_score}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Completion */}
            <div className="card">
              <h3 className="font-semibold text-slate-700 mb-3 flex items-center gap-2"><Clock className="w-4 h-4 text-brand-600" /> Completion</h3>
              <div className="text-3xl font-bold text-brand-600">{detail.completion_pct}%</div>
              <p className="text-xs text-slate-400 mt-1">{posts.filter((p: any) => p.status === 'Posted').length} of {posts.length} posts published</p>
            </div>
          </div>

          {/* Prime times */}
          <div className="card mb-6">
            <h3 className="font-semibold text-slate-700 mb-3">Prime Time Posting</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-slate-400 text-left"><th className="pb-2 pr-4">Day</th><th className="pb-2 pr-4">Platform</th><th className="pb-2">Best Time</th></tr></thead>
                <tbody>
                  {(detail.prime_times || []).slice(0, 14).map((t: any, i: number) => (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="py-1.5 pr-4 text-slate-600">{t.day}</td>
                      <td className="py-1.5 pr-4 text-slate-600">{t.platform}</td>
                      <td className="py-1.5 font-medium text-slate-700">{t.best_time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Content calendar / posts table */}
          <div className="card">
            <h3 className="font-semibold text-slate-700 mb-3">Content Calendar — {detail.month}</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 text-left">
                    <th className="pb-2 pr-3">Date</th>
                    <th className="pb-2 pr-3">Platform</th>
                    <th className="pb-2 pr-3">Type</th>
                    <th className="pb-2 pr-3">Caption</th>
                    <th className="pb-2 pr-3">CTA</th>
                    <th className="pb-2 pr-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {pagePosts.map((p: any) => (
                    <tr key={p.id} className="border-t border-slate-100 align-top">
                      <td className="py-2 pr-3 whitespace-nowrap text-slate-600">{p.date}</td>
                      <td className="py-2 pr-3 whitespace-nowrap text-slate-600">{p.platform}</td>
                      <td className="py-2 pr-3 whitespace-nowrap text-slate-600">{p.post_type}</td>
                      <td className="py-2 pr-3 text-slate-700 max-w-xs truncate" title={p.caption}>{p.caption}</td>
                      <td className="py-2 pr-3 whitespace-nowrap text-slate-600">{p.cta}</td>
                      <td className="py-2 pr-3">
                        <select
                          value={p.status}
                          onChange={(e) => handleStatusChange(p.id, e.target.value)}
                          className={clsx(
                            'text-xs rounded-lg px-2 py-1 border',
                            p.status === 'Posted' && 'bg-emerald-50 text-emerald-700 border-emerald-200',
                            p.status === 'Missed' && 'bg-red-50 text-red-700 border-red-200',
                            p.status === 'Pending' && 'bg-slate-50 text-slate-600 border-slate-200'
                          )}
                        >
                          <option value="Pending">Pending</option>
                          <option value="Posted">Posted</option>
                          <option value="Missed">Missed</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-4">
              <span className="text-xs text-slate-400">Page {page} of {totalPages}</span>
              <div className="flex gap-2">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1 disabled:opacity-40">
                  <ChevronLeft className="w-3.5 h-3.5" /> Prev
                </button>
                <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1 disabled:opacity-40">
                  Next <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
