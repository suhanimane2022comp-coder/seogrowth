'use client'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { getReport, getPdfReport, getJsonReport } from '@/lib/api'
import Cookies from "js-cookie";
import {
  Download, AlertTriangle, CheckCircle2, Info, Search,
  FileText, Lightbulb, TrendingUp, ChevronDown, ChevronUp, ExternalLink
} from 'lucide-react'

interface ReportData {
  executive_summary: any
  seo_scores: any
  technical_seo: any
  keyword_opportunities: any
  content_gaps: any
  generated_content: any
  improvement_plan: any[]
  generated_at: string
}

function isContactPageItem(item: string) {
  return /contact/i.test(item)
}

// ── Score bar (PDF-style horizontal metric row) ──────────────────────────────
function ScoreBar({ label, score }: { label: string; score: number }) {
  const pct = Math.min(100, Math.max(0, score))
  const color =
    pct >= 80 ? '#16a34a' : pct >= 60 ? '#2563eb' : pct >= 40 ? '#d97706' : '#dc2626'
  const rating =
    pct >= 80 ? 'Excellent' : pct >= 60 ? 'Good' : pct >= 40 ? 'Fair' : 'Poor'

  return (
    <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
      <td style={{ padding: '10px 0', fontSize: 14, color: '#334155', width: '40%' }}>{label}</td>
      <td style={{ padding: '10px 12px', width: '40%' }}>
        <div style={{ background: '#e2e8f0', borderRadius: 4, height: 8 }}>
          <div style={{ width: `${pct}%`, height: 8, borderRadius: 4, background: color, transition: 'width 0.6s ease' }} />
        </div>
      </td>
      <td style={{ padding: '10px 0', fontSize: 14, fontWeight: 600, color, whiteSpace: 'nowrap' }}>
        {pct.toFixed(1)}/100
      </td>
      <td style={{ padding: '10px 0 10px 12px', fontSize: 13, color: '#64748b' }}>{rating}</td>
    </tr>
  )
}

// ── Section block matching PDF section styling ────────────────────────────────
function Section({ title, children, defaultOpen = true }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div style={{ marginBottom: 28 }}>
      {/* Section header – dark bar like PDF */}
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          width: '100%', textAlign: 'left', background: '#1e293b',
          color: '#fff', padding: '10px 16px', borderRadius: 6,
          border: 'none', cursor: 'pointer', marginBottom: open ? 16 : 0,
          fontSize: 14, fontWeight: 600, letterSpacing: 0.2
        }}
      >
        <span>{title}</span>
        {open
          ? <ChevronUp style={{ width: 16, height: 16, opacity: 0.7 }} />
          : <ChevronDown style={{ width: 16, height: 16, opacity: 0.7 }} />}
      </button>
      {open && <div>{children}</div>}
    </div>
  )
}

// ── Pill badge ─────────────────────────────────────────────────────────────────
function Pill({ label, color }: { label: string; color: string }) {
  const map: Record<string, { bg: string; text: string }> = {
    red: { bg: '#fef2f2', text: '#b91c1c' },
    amber: { bg: '#fffbeb', text: '#92400e' },
    blue: { bg: '#eff6ff', text: '#1d4ed8' },
  }
  const { bg, text } = map[color] || map.blue
  return (
    <span style={{
      display: 'inline-block', padding: '3px 10px', borderRadius: 999,
      fontSize: 12, fontWeight: 600, background: bg, color: text, marginRight: 6
    }}>{label}</span>
  )
}

// ── Issue row ──────────────────────────────────────────────────────────────────
function IssueItem({ issue }: { issue: any }) {
  const isWarning = issue.severity === 'warning'
  const isCritical = issue.severity === 'critical'
  const dot = isCritical ? '#dc2626' : isWarning ? '#d97706' : '#3b82f6'
  const label = isCritical ? 'Critical' : isWarning ? 'Warning' : 'Info'
  const pillColor = isCritical ? 'red' : isWarning ? 'amber' : 'blue'

  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 12,
      padding: '10px 0', borderBottom: '1px solid #f8fafc'
    }}>
      <span style={{ marginTop: 5, width: 8, height: 8, borderRadius: '50%', background: dot, flexShrink: 0 }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <Pill label={label} color={pillColor} />
          <span style={{ fontSize: 14, color: '#334155', fontWeight: 500 }}>
            {issue.issue_type?.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}
          </span>
        </div>
        {issue.page_url && (
          <p style={{ fontSize: 12, color: '#6366f1', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {issue.page_url}
          </p>
        )}
      </div>
    </div>
  )
}

// ── Keyword chip ───────────────────────────────────────────────────────────────
function KeywordChip({ label }: { label: string }) {
  return (
    <span style={{
      display: 'inline-block', margin: '3px 4px 3px 0',
      padding: '4px 10px', borderRadius: 999, fontSize: 12,
      background: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0'
    }}>{label}</span>
  )
}

// ── Gap item ───────────────────────────────────────────────────────────────────
function GapItem({ text }: { text: string }) {
  return (
    <li style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 6 }}>
      <span style={{ color: '#6366f1', fontSize: 16, lineHeight: 1.4, flexShrink: 0 }}>•</span>
      <span style={{ fontSize: 14, color: '#334155' }}>{text}</span>
    </li>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function ReportDetailPage() {
  const { id } = useParams()
  const [report, setReport] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    getReport(Number(id))
      .then(({ data }) => setReport(data.report_data))
      .catch(() => setError('Report not found or still processing.'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 384 }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          width: 40, height: 40, border: '4px solid #6366f1',
          borderTopColor: 'transparent', borderRadius: '50%',
          animation: 'spin 0.8s linear infinite', margin: '0 auto 16px'
        }} />
        <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
        <p style={{ color: '#64748b', fontSize: 14 }}>Loading report…</p>
      </div>
    </div>
  )

  if (error || !report) return (
    <div style={{ maxWidth: 480, margin: '80px auto', textAlign: 'center', padding: 32 }}>
      <AlertTriangle style={{ width: 40, height: 40, color: '#f59e0b', margin: '0 auto 12px' }} />
      <p style={{ fontWeight: 600, color: '#334155' }}>{error || 'Report unavailable'}</p>
      <p style={{ fontSize: 14, color: '#94a3b8', marginTop: 4 }}>The analysis may still be running. Refresh in a minute.</p>
    </div>
  )

  const summary = report.executive_summary || {}
  const scores = report.seo_scores || {}
  const issues = report.technical_seo?.issues || []
  const keywords = report.keyword_opportunities || {}
  const gaps = report.content_gaps || {}
  const content = report.generated_content || {}
  const plan = report.improvement_plan || []

  const pdfUrl = getPdfReport(Number(id))
  const jsonUrl = getJsonReport(Number(id))
  const downloadPdf = () => {
    const token = Cookies.get("token")
    window.open(`${pdfUrl}?token=${token}`, "_blank")
  }

  const overallScore = scores.overall_score ?? 0
  const gradeColor =
    overallScore >= 80 ? '#16a34a' : overallScore >= 60 ? '#2563eb' : overallScore >= 40 ? '#d97706' : '#dc2626'
  const gradeBg =
    overallScore >= 80 ? '#f0fdf4' : overallScore >= 60 ? '#eff6ff' : overallScore >= 40 ? '#fffbeb' : '#fef2f2'

  // ─── styles ───
  const card: React.CSSProperties = {
    background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8,
    padding: '20px 24px', marginBottom: 20
  }
  const sectionLabel: React.CSSProperties = {
    fontSize: 11, fontWeight: 700, color: '#94a3b8',
    textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10
  }

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', fontFamily: 'system-ui, sans-serif', color: '#1e293b' }}>

      {/* ── Report title bar ── */}
      <div style={{ ...card, background: '#1e293b', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <p style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 4 }}>
            SEO Growth Report
          </p>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>{summary.business_name || 'SEO Report'}</h1>
          <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 4 }}>
            Generated {report.generated_at ? new Date(report.generated_at).toLocaleString() : ''}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <a href={jsonUrl} target="_blank" rel="noopener noreferrer" style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '8px 14px', borderRadius: 6, fontSize: 13, fontWeight: 500,
            background: 'transparent', border: '1px solid #475569', color: '#cbd5e1', textDecoration: 'none'
          }}>
            <Download style={{ width: 15, height: 15 }} /> JSON
          </a>
          <button onClick={downloadPdf} style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '8px 14px', borderRadius: 6, fontSize: 13, fontWeight: 500,
            background: '#6366f1', border: 'none', color: '#fff', cursor: 'pointer'
          }}>
            <Download style={{ width: 15, height: 15 }} /> PDF
          </button>
        </div>
      </div>

      {/* ── SEO Scores ── */}
      <div style={card}>
        <p style={{ ...sectionLabel }}>SEO Scores</p>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
              <th style={{ textAlign: 'left', fontSize: 13, color: '#64748b', fontWeight: 600, paddingBottom: 8 }}>Metric</th>
              <th style={{ width: '40%' }} />
              <th style={{ textAlign: 'left', fontSize: 13, color: '#64748b', fontWeight: 600, paddingBottom: 8 }}>Score</th>
              <th style={{ textAlign: 'left', fontSize: 13, color: '#64748b', fontWeight: 600, paddingBottom: 8, paddingLeft: 12 }}>Rating</th>
            </tr>
          </thead>
          <tbody>
            <ScoreBar label="Overall SEO Score" score={scores.overall_score ?? 0} />
            <ScoreBar label="Technical SEO" score={scores.technical_score ?? 0} />
            <ScoreBar label="Content Quality" score={scores.content_score ?? 0} />
            <ScoreBar label="Keyword Coverage" score={scores.keyword_score ?? 0} />
            <ScoreBar label="Metadata Quality" score={scores.metadata_score ?? 0} />
          </tbody>
        </table>

        {/* Grade */}
        <div style={{ marginTop: 16, display: 'inline-block', padding: '6px 20px', borderRadius: 999, background: gradeBg, color: gradeColor, fontWeight: 700, fontSize: 15 }}>
          Grade: {summary.grade} — {summary.grade_label}
        </div>
      </div>

      {/* ── Executive Summary ── */}
      <Section title="Executive Summary">
        <p style={{ fontSize: 14, color: '#334155', lineHeight: 1.8 }}>{summary.summary}</p>
      </Section>

      {/* ── SEO Issues ── */}
      {issues.length > 0 && (() => {
        const critical = issues.filter((i: any) => i.severity === 'critical')
        const warnings = issues.filter((i: any) => i.severity === 'warning')
        const info = issues.filter((i: any) => i.severity === 'info')

        // Group issues by type, collecting all affected URLs
        const groupByType = (group: any[]) => {
          const map = new Map<string, { description: string; urls: string[] }>()
          group.forEach((issue: any) => {
            const key = issue.issue_type || 'unknown'
            if (!map.has(key)) {
              map.set(key, {
                description: issue.description || '',
                urls: []
              })
            }
            if (issue.page_url) map.get(key)!.urls.push(issue.page_url)
          })
          return Array.from(map.entries())
        }

        const renderGroup = (group: any[], label: string, color: string) =>
          group.length > 0 ? (
            <div style={{ marginBottom: 20 }}>
              <p style={{ fontSize: 15, fontWeight: 700, fontStyle: 'italic', color, marginBottom: 10 }}>
                {label} ({groupByType(group).length})
              </p>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {groupByType(group).map(([type, data], i) => (
                  <li key={i} style={{ display: 'flex', gap: 6, fontSize: 14, color: '#334155', lineHeight: 1.6, marginBottom: 8 }}>
                    <span style={{ flexShrink: 0 }}>•</span>
                    <span>
                      <strong>{type.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}</strong>
                      {data.description && <>: {data.description}</>}
                      {data.urls.length > 0 && (
                        <span style={{ display: 'block', marginTop: 2 }}>
                          {data.urls.map((url, j) => (
                            <span key={j} style={{ fontStyle: 'italic', color: '#64748b', display: 'block', fontSize: 13 }}>
                              ({url})
                            </span>
                          ))}
                        </span>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null

        return (
          <Section title={`SEO Issues Found`}>
            {renderGroup(critical, 'Critical Issues', '#b91c1c')}
            {renderGroup(warnings, 'Warnings', '#92400e')}
            {renderGroup(info, 'Info', '#1d4ed8')}
          </Section>
        )
      })()}

      {/* ── Keywords ── */}
      <Section title="Keyword Opportunities">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
          {Object.entries(keywords).map(([type, kws]: [string, any]) =>
            kws?.length > 0 ? (
              <div key={type}>
                <p style={sectionLabel}>{type.replace(/_/g, ' ')}</p>
                <div>
                  {(kws as string[]).map((kw: string, i: number) => (
                    <KeywordChip key={i} label={kw} />
                  ))}
                </div>
              </div>
            ) : null
          )}
        </div>
      </Section>

      {/* ── Content Gap Analysis ── */}
      <Section title="Content Gap Analysis">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20 }}>
          {Object.entries(gaps).map(([type, items]: [string, any]) => {
            const filtered = ((items as string[]) || []).filter(item => !isContactPageItem(item))
            return filtered.length > 0 ? (
              <div key={type}>
                <p style={sectionLabel}>{type.replace(/_/g, ' ')}</p>
                <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                  {filtered.map((item: string, i: number) => <GapItem key={i} text={item} />)}
                </ul>
              </div>
            ) : null
          })}
        </div>
      </Section>

      {/* ── Generated FAQs ── */}
      {content.faqs?.length > 0 && (
        <Section title={`Generated FAQs (${content.faqs.length})`} defaultOpen={false}>
          <div>
            {content.faqs.map((faq: any, i: number) => (
              <div key={i} style={{ borderBottom: '1px solid #f1f5f9', paddingBottom: 16, marginBottom: 16 }}>
                <p style={{ fontWeight: 600, fontSize: 14, color: '#1e293b', marginBottom: 6 }}>
                  Q: {faq.question}
                </p>
                <p style={{ fontSize: 14, color: '#475569', lineHeight: 1.6 }}>A: {faq.answer}</p>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── Blog Ideas ── */}
      {content.blog_ideas?.length > 0 && (
        <Section title="Blog Content Ideas" defaultOpen={false}>
          {content.blog_ideas.map((blog: any, i: number) => (
            <div key={i} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '14px 16px', marginBottom: 12 }}>
              <p style={{ fontWeight: 600, fontSize: 14, color: '#1e293b', marginBottom: 4 }}>{blog.title}</p>
              {blog.outline && <p style={{ fontSize: 13, color: '#64748b', marginBottom: 8 }}>{blog.outline}</p>}
              <span style={{
                display: 'inline-block', fontSize: 12, padding: '3px 10px', borderRadius: 999,
                background: '#eef2ff', color: '#4338ca'
              }}>
                🎯 {blog.target_keyword}
              </span>
            </div>
          ))}
        </Section>
      )}

      {/* ── Generated Metadata ── */}
      {content.metadata?.length > 0 && (
        <Section title="Generated Metadata" defaultOpen={false}>
          {content.metadata.map((m: any, i: number) => (
            <div key={i} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '14px 16px', marginBottom: 12 }}>
              <p style={{ fontSize: 12, fontWeight: 600, color: '#94a3b8', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>{m.page}</p>
              <p style={{ fontSize: 14, fontWeight: 600, color: '#1e293b', marginBottom: 4 }}>Title: {m.title}</p>
              <p style={{ fontSize: 14, color: '#475569' }}>Description: {m.description}</p>
            </div>
          ))}
        </Section>
      )}

      {/* ── Improvement Plan ── */}
      {plan.length > 0 && (
        <Section title="Improvement Plan">
          {plan.map((item: any, i: number) => {
            const filteredTasks = (item.tasks || []).filter((t: string) => !isContactPageItem(t))
            if (!filteredTasks.length) return null
            return (
              <div key={i} style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
                <div style={{
                  flexShrink: 0, width: 32, height: 32, borderRadius: '50%',
                  background: '#6366f1', color: '#fff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 13, fontWeight: 700
                }}>
                  {item.priority}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
                    <p style={{ fontWeight: 600, fontSize: 14, color: '#1e293b', margin: 0 }}>{item.action}</p>
                    <span style={{
                      fontSize: 12, background: '#f1f5f9', color: '#64748b',
                      padding: '2px 10px', borderRadius: 999
                    }}>{item.timeframe}</span>
                  </div>
                  <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
                    {filteredTasks.map((task: string, j: number) => (
                      <li key={j} style={{ fontSize: 13, color: '#475569', marginBottom: 4, display: 'flex', gap: 8 }}>
                        <span style={{ color: '#6366f1', flexShrink: 0 }}>•</span> {task}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )
          })}
        </Section>
      )}

      {/* ── Technical Recommendations ── */}
      {(content.schema_suggestions?.length > 0 || content.internal_linking_suggestions?.length > 0) && (
        <Section title="Technical Recommendations" defaultOpen={false}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 24 }}>
            {content.schema_suggestions?.length > 0 && (
              <div>
                <p style={sectionLabel}>Schema Markup</p>
                <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                  {content.schema_suggestions.map((s: string, i: number) => (
                    <li key={i} style={{ display: 'flex', gap: 8, fontSize: 14, color: '#334155', marginBottom: 6 }}>
                      <CheckCircle2 style={{ width: 15, height: 15, color: '#16a34a', flexShrink: 0, marginTop: 2 }} /> {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {content.internal_linking_suggestions?.length > 0 && (
              <div>
                <p style={sectionLabel}>Internal Linking</p>
                <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                  {content.internal_linking_suggestions.map((s: string, i: number) => (
                    <li key={i} style={{ display: 'flex', gap: 8, fontSize: 14, color: '#334155', marginBottom: 6 }}>
                      <ExternalLink style={{ width: 15, height: 15, color: '#3b82f6', flexShrink: 0, marginTop: 2 }} /> {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Section>
      )}

      {/* ── Footer export ── */}
      <div style={{ ...card, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <p style={{ fontWeight: 600, color: '#1e293b', marginBottom: 2 }}>Export Full Report</p>
          <p style={{ fontSize: 13, color: '#64748b' }}>Download the complete analysis in your preferred format</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <a href={jsonUrl} target="_blank" rel="noopener noreferrer" style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '8px 14px', borderRadius: 6, fontSize: 13, fontWeight: 500,
            background: '#fff', border: '1px solid #e2e8f0', color: '#475569', textDecoration: 'none'
          }}>
            <Download style={{ width: 15, height: 15 }} /> JSON
          </a>
          <button onClick={downloadPdf} style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '8px 14px', borderRadius: 6, fontSize: 13, fontWeight: 500,
            background: '#6366f1', border: 'none', color: '#fff', cursor: 'pointer'
          }}>
            <Download style={{ width: 15, height: 15 }} /> PDF
          </button>
        </div>
      </div>

      <p style={{ textAlign: 'center', fontSize: 12, color: '#94a3b8', marginTop: 8, paddingBottom: 32 }}>
        Report generated by SEO Growth AI Agent
      </p>
    </div>
  )
}