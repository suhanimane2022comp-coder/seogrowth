'use client'
import { useEffect, useState } from 'react'
import { generatePromptAgent, getLatestPromptAgent } from '@/lib/api'
import { Sparkles, Loader2, Copy, Check, ChevronDown, ChevronUp } from 'lucide-react'

export default function PromptsPage() {
  const [output, setOutput] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)
  const [error, setError] = useState('')
  const [copiedKey, setCopiedKey] = useState('')
  const [openOccasion, setOpenOccasion] = useState<string | null>(null)

  const fetchLatest = async () => {
    try {
      const { data } = await getLatestPromptAgent()
      setOutput(data)
    } catch {}
    setFetching(false)
  }

  useEffect(() => { fetchLatest() }, [])

  const handleGenerate = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await generatePromptAgent()
      setOutput(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate prompts')
    } finally {
      setLoading(false)
    }
  }

  const copy = (key: string, text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(''), 1500)
  }

  const wp = output?.website_prompt
  const seasonal = output?.seasonal_content || {}

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Content &amp; Website Prompt Agent</h1>
          <p className="text-slate-500 text-sm mt-1">Generate a website build prompt and seasonal social content, based on your latest SEO report.</p>
        </div>
        <button onClick={handleGenerate} disabled={loading} className="btn-primary flex items-center gap-2">
          {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</> : <><Sparkles className="w-4 h-4" /> Generate</>}
        </button>
      </div>

      {error && <div className="bg-red-50 text-red-600 text-sm rounded-xl px-4 py-3 mb-6">{error}</div>}

      {fetching ? (
        <div className="card text-center py-12 text-slate-400">Loading...</div>
      ) : !output ? (
        <div className="card text-center py-16">
          <Sparkles className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="font-semibold text-slate-600 mb-2">No prompts generated yet</h3>
          <p className="text-slate-400 text-sm mb-6">Run an SEO analysis first, then click Generate to create a website prompt and seasonal content.</p>
          <button onClick={handleGenerate} disabled={loading} className="btn-primary inline-flex items-center gap-2">
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</> : <><Sparkles className="w-4 h-4" /> Generate Now</>}
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Website Prompt */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-slate-800">Lovable Website Prompt</h2>
              <button
                onClick={() => copy('full', JSON.stringify(wp, null, 2))}
                className="btn-secondary text-xs flex items-center gap-1.5 py-1.5 px-3"
              >
                {copiedKey === 'full' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />} Copy All
              </button>
            </div>

            <Section title="Homepage Structure">
              {wp?.homepage_structure && Object.entries(wp.homepage_structure).map(([k, v]: any) => (
                <Field key={k} label={k.replace(/_/g, ' ')} value={Array.isArray(v) ? v.join(' • ') : v} />
              ))}
            </Section>

            <Section title="SEO Details">
              {wp?.seo_details && Object.entries(wp.seo_details).map(([k, v]: any) => (
                <Field key={k} label={k.replace(/_/g, ' ')} value={Array.isArray(v) ? v.join(' • ') : v} />
              ))}
            </Section>

            <Section title="Keyword Placement">
              {wp?.keyword_placement && Object.entries(wp.keyword_placement).map(([k, v]: any) => (
                <Field key={k} label={k.replace(/_/g, ' ')} value={Array.isArray(v) ? v.join(', ') : v} />
              ))}
            </Section>

            <Section title="Conversion Suggestions">
              {wp?.conversion_suggestions && Object.entries(wp.conversion_suggestions).map(([k, v]: any) => (
                <Field key={k} label={k.replace(/_/g, ' ')} value={Array.isArray(v) ? v.join(', ') : v} />
              ))}
            </Section>
          </div>

          {/* Seasonal Content */}
          <div className="card">
            <h2 className="font-semibold text-slate-800 mb-4">Seasonal Content Generator</h2>
            <div className="space-y-2">
              {Object.keys(seasonal).map((occ) => (
                <div key={occ} className="border border-slate-100 rounded-xl">
                  <button
                    className="w-full flex items-center justify-between px-4 py-3 text-left"
                    onClick={() => setOpenOccasion(openOccasion === occ ? null : occ)}
                  >
                    <span className="font-medium text-slate-700">{occ}</span>
                    {openOccasion === occ ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                  </button>
                  {openOccasion === occ && (
                    <div className="px-4 pb-4 space-y-3">
                      {Object.entries(seasonal[occ].captions || {}).map(([platform, caption]: any) => (
                        <div key={platform} className="bg-slate-50 rounded-xl p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-semibold text-slate-500 uppercase">{platform}</span>
                            <button onClick={() => copy(`${occ}-${platform}`, caption)} className="text-slate-400 hover:text-brand-600">
                              {copiedKey === `${occ}-${platform}` ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                            </button>
                          </div>
                          <p className="text-sm text-slate-700">{caption}</p>
                        </div>
                      ))}
                      <div className="bg-indigo-50 rounded-xl p-3">
                        <span className="text-xs font-semibold text-indigo-500 uppercase">AI Image Prompt</span>
                        <p className="text-sm text-slate-700 mt-1">{seasonal[occ].image_prompt}</p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-5">
      <h3 className="text-sm font-semibold text-brand-700 mb-2">{title}</h3>
      <div className="space-y-1.5">{children}</div>
    </div>
  )
}

function Field({ label, value }: { label: string; value: any }) {
  return (
    <div className="text-sm flex gap-2">
      <span className="text-slate-400 capitalize flex-shrink-0 w-40">{label}:</span>
      <span className="text-slate-700">{String(value)}</span>
    </div>
  )
}
