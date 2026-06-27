'use client'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { getReport, getPdfReport, getJsonReport } from '@/lib/api'
import ScoreRing from '@/components/ScoreRing'
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

// Returns true for any gap item or task that refers to a missing contact page,
// so it can be filtered out of the Content Gap Analysis and Improvement Plan sections.
function isContactPageItem(item: string) {
  return /contact/i.test(item)
}

function Section({ title, icon: Icon, children, defaultOpen = true }: any) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="card mb-4">
      <button onClick={() => setOpen((o: boolean) => !o)}
        className="flex items-center justify-between w-full text-left">
        <div className="flex items-center gap-2">
          <Icon className="w-5 h-5 text-brand-600" />
          <h2 className="font-semibold text-slate-800">{title}</h2>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </button>
      {open && <div className="mt-5">{children}</div>}
    </div>
  )
}

function IssueItem({ issue }: { issue: any }) {
  const map: any = {
    critical: { cls: 'badge-critical', Icon: AlertTriangle },
    warning: { cls: 'badge-warning', Icon: AlertTriangle },
    info: { cls: 'badge-info', Icon: Info },
  }
  const { cls, Icon } = map[issue.severity] ?? map.info
  return (
    <div className="flex items-start gap-3 py-3 border-b border-slate-50 last:border-0">
      <span className={cls}><Icon className="w-3 h-3 mr-1" />{issue.severity}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-700">{issue.issue_type?.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}</p>
       
        {issue.page_url && <p className="text-xs text-brand-500 mt-0.5 truncate">{issue.page_url}</p>}
      </div>
    </div>
  )
}

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
    <div className="flex items-center justify-center h-96">
      <div className="text-center">
        <div className="animate-spin w-10 h-10 border-4 border-brand-600 border-t-transparent rounded-full mx-auto mb-4" />
        <p className="text-slate-500">Loading report…</p>
      </div>
    </div>
  )

  if (error || !report) return (
    <div className="card text-center py-16 max-w-lg mx-auto">
      <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto mb-3" />
      <p className="text-slate-600 font-semibold">{error || 'Report unavailable'}</p>
      <p className="text-slate-400 text-sm mt-1">The analysis may still be running. Refresh in a minute.</p>
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
  const token = Cookies.get("token");

  window.open(
    `${pdfUrl}?token=${token}`,
    "_blank"
  );
};

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">{summary.business_name}</h1>
          <p className="text-slate-500 text-sm mt-0.5">Generated {report.generated_at ? new Date(report.generated_at).toLocaleString() : ''}</p>
        </div>
        <div className="flex gap-2">
          <a href={jsonUrl} target="_blank" rel="noopener noreferrer"
            className="btn-secondary flex items-center gap-2 text-sm py-2">
            <Download className="w-4 h-4" /> JSON
          </a>
        <button
  onClick={downloadPdf}
  className="btn-primary flex items-center gap-2 text-sm py-2"
>
  <Download className="w-4 h-4" />
  PDF
</button>
        </div>
      </div>

      {/* Score Overview */}
      <div className="card mb-4">
        <h2 className="font-semibold text-slate-800 mb-5">SEO Score Overview</h2>
        <div className="flex flex-wrap justify-around gap-6">
          <ScoreRing score={scores.overall_score ?? 0} size={130} label="Overall" />
          <ScoreRing score={scores.technical_score ?? 0} size={100} label="Technical" />
          <ScoreRing score={scores.content_score ?? 0} size={100} label="Content" />
          <ScoreRing score={scores.keyword_score ?? 0} size={100} label="Keywords" />
          <ScoreRing score={scores.metadata_score ?? 0} size={100} label="Metadata" />
        </div>

        {/* Grade badge */}
        <div className="mt-5 text-center">
          <span className={`inline-block px-6 py-2 rounded-full text-lg font-bold ${
            (scores.overall_score ?? 0) >= 80 ? 'bg-emerald-100 text-emerald-700' :
            (scores.overall_score ?? 0) >= 60 ? 'bg-blue-100 text-blue-700' :
            (scores.overall_score ?? 0) >= 40 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'
          }`}>
            Grade: {summary.grade} — {summary.grade_label}
          </span>
        </div>
      </div>

      {/* Executive Summary */}
      <Section title="Executive Summary" icon={FileText}>
        <p className="text-slate-600 text-sm leading-relaxed mb-4">{summary.summary}</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Pages Analyzed', value: summary.pages_analyzed ?? 0 },
            { label: 'Total Issues', value: summary.total_issues ?? 0 },
            { label: 'Critical Issues', value: summary.critical_issues ?? 0 },
            { label: 'Keywords Found', value: summary.keyword_opportunities ?? 0 },
          ].map(({ label, value }) => (
            <div key={label} className="bg-slate-50 rounded-xl p-3 text-center">
              <div className="text-2xl font-bold text-slate-800">{value}</div>
              <div className="text-xs text-slate-500 mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      </Section>

      {/* Technical SEO Issues */}
      {issues.length > 0 && (
        <Section title={`SEO Issues (${issues.length})`} icon={AlertTriangle}>
          <div className="mb-3 flex gap-2 flex-wrap">
            <span className="badge-critical">{issues.filter((i: any) => i.severity === 'critical').length} Critical</span>
            <span className="badge-warning">{issues.filter((i: any) => i.severity === 'warning').length} Warnings</span>
            <span className="badge-info">{issues.filter((i: any) => i.severity === 'info').length} Info</span>
          </div>
          <div className="divide-y divide-slate-50">
            {issues.slice(0, 20).map((issue: any, i: number) => <IssueItem key={i} issue={issue} />)}
            {issues.length > 20 && <p className="text-xs text-slate-400 pt-2">…and {issues.length - 20} more in the full report.</p>}
          </div>
        </Section>
      )}

      {/* Keywords */}
      <Section title="Keyword Opportunities" icon={Search}>
        <div className="grid md:grid-cols-2 gap-4">
          {Object.entries(keywords).map(([type, kws]: [string, any]) =>
            kws?.length > 0 ? (
              <div key={type} className="bg-slate-50 rounded-xl p-4">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">
                  {type.replace(/_/g, ' ')}
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {(kws as string[]).map((kw: string, i: number) => (
                    <span key={i} className="bg-white border border-slate-200 text-slate-700 text-xs px-2.5 py-1 rounded-full">{kw}</span>
                  ))}
                </div>
              </div>
            ) : null
          )}
        </div>
      </Section>

      {/* Content Gaps */}
      <Section title="Content Gap Analysis" icon={TrendingUp}>
        <div className="grid md:grid-cols-2 gap-4">
          {Object.entries(gaps).map(([type, items]: [string, any]) => {
            const filteredItems = ((items as string[]) || []).filter(
              (item: string) => !isContactPageItem(item)
            )
            return filteredItems.length > 0 ? (
              <div key={type}>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">
                  {type.replace(/_/g, ' ')}
                </h4>
                <ul className="space-y-1">
                  {filteredItems.map((item: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                      <CheckCircle2 className="w-4 h-4 text-brand-400 mt-0.5 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null
          })}
        </div>
      </Section>

      {/* Generated Metadata */}
      {content.metadata?.length > 0 && (
        <Section title="Generated Metadata" icon={FileText} defaultOpen={false}>
          <div className="space-y-3">
            {content.metadata.map((m: any, i: number) => (
              <div key={i} className="bg-slate-50 rounded-xl p-4">
                <p className="text-xs font-semibold text-slate-500 mb-1">{m.page}</p>
                <p className="text-sm font-semibold text-slate-800 mb-0.5">Title: {m.title}</p>
                <p className="text-sm text-slate-600">Description: {m.description}</p>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* FAQs */}
      {content.faqs?.length > 0 && (
        <Section title={`Generated FAQs (${content.faqs.length})`} icon={Lightbulb} defaultOpen={false}>
          <div className="space-y-4">
            {content.faqs.map((faq: any, i: number) => (
              <div key={i} className="border-b border-slate-100 pb-4 last:border-0">
                <p className="font-semibold text-slate-800 text-sm mb-1">Q: {faq.question}</p>
                <p className="text-slate-600 text-sm">A: {faq.answer}</p>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Blog Ideas */}
      {content.blog_ideas?.length > 0 && (
        <Section title="Blog Content Ideas" icon={FileText} defaultOpen={false}>
          <div className="grid gap-3">
            {content.blog_ideas.map((blog: any, i: number) => (
              <div key={i} className="bg-slate-50 rounded-xl p-4">
                <p className="font-semibold text-slate-800 text-sm">{blog.title}</p>
                <p className="text-slate-500 text-xs mt-1">{blog.outline}</p>
                <span className="inline-block mt-2 text-xs bg-brand-100 text-brand-700 px-2 py-0.5 rounded-full">
                  🎯 {blog.target_keyword}
                </span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Improvement Plan */}
      {plan.length > 0 && (
        <Section title="Improvement Plan" icon={TrendingUp}>
          <div className="space-y-4">
            {plan.map((item: any, i: number) => {
              const filteredTasks = (item.tasks || []).filter(
                (task: string) => !isContactPageItem(task)
              )
              if (filteredTasks.length === 0) return null
              return (
                <div key={i} className="flex gap-4">
                  <div className="flex-shrink-0 w-8 h-8 bg-brand-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                    {item.priority}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-semibold text-slate-800 text-sm">{item.action}</p>
                      <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">{item.timeframe}</span>
                    </div>
                    <ul className="space-y-0.5">
                      {filteredTasks.map((task: string, j: number) => (
                        <li key={j} className="text-xs text-slate-600 flex items-start gap-1.5">
                          <span className="text-brand-400 mt-0.5">•</span> {task}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )
            })}
          </div>
        </Section>
      )}

      {/* Schema & Internal Linking */}
      {(content.schema_suggestions?.length > 0 || content.internal_linking_suggestions?.length > 0) && (
        <Section title="Technical Recommendations" icon={CheckCircle2} defaultOpen={false}>
          <div className="grid md:grid-cols-2 gap-4">
            {content.schema_suggestions?.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Schema Markup</h4>
                <ul className="space-y-1">
                  {content.schema_suggestions.map((s: string, i: number) => (
                    <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />{s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {content.internal_linking_suggestions?.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Internal Linking</h4>
                <ul className="space-y-1">
                  {content.internal_linking_suggestions.map((s: string, i: number) => (
                    <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                      <ExternalLink className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />{s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Download again at bottom */}
      <div className="card mt-4 flex items-center justify-between">
        <div>
          <p className="font-semibold text-slate-800">Export Full Report</p>
          <p className="text-slate-500 text-sm">Download the complete analysis in your preferred format</p>
        </div>
        <div className="flex gap-2">
          <a href={jsonUrl} target="_blank" rel="noopener noreferrer" className="btn-secondary flex items-center gap-2 text-sm">
            <Download className="w-4 h-4" /> JSON
          </a>
       <button
  onClick={downloadPdf}
  className="btn-primary flex items-center gap-2 text-sm py-2"
>
  <Download className="w-4 h-4" />
  PDF
</button>
        </div>
      </div>
    </div>
  )
}