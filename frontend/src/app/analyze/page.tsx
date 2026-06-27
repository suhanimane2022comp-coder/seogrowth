'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createProject } from '@/lib/api'
import { Loader2, Zap, Globe } from 'lucide-react'

export default function AnalyzePage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [websiteUrl, setWebsiteUrl] = useState('')

  const isValidUrl = (value: string) => {
    try {
      const u = new URL(value)
      return u.protocol === 'http:' || u.protocol === 'https:'
    } catch {
      return false
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!websiteUrl.trim()) {
      setError('Website URL is required')
      return
    }
    if (!isValidUrl(websiteUrl.trim())) {
      setError('Please enter a valid URL, e.g. https://example.com')
      return
    }
    setLoading(true)
    try {
      await createProject({ website_url: websiteUrl.trim() })
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start analysis')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-800">New SEO Analysis</h1>
        <p className="text-slate-500 text-sm mt-1">
          We'll use your saved business profile, audience, and competitors automatically — just give us the website to analyze.
        </p>
      </div>

      {error && <div className="bg-red-50 text-red-600 text-sm rounded-xl px-4 py-3 mb-6">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card">
          <div className="flex items-center gap-2 mb-5">
            <Globe className="w-5 h-5 text-brand-600" />
            <h2 className="font-semibold text-slate-700">Website URL</h2>
          </div>
          <input
            className="input"
            placeholder="https://yourwebsite.com"
            value={websiteUrl}
            onChange={(e) => setWebsiteUrl(e.target.value)}
            required
          />
          <p className="text-xs text-slate-400 mt-2">
            The AI will crawl and audit this site, using your profile's keywords, audience persona, and competitors.
          </p>
        </div>

        <div className="bg-gradient-to-r from-brand-50 to-indigo-50 border border-brand-100 rounded-2xl p-5">
          <div className="flex items-start gap-3">
            <Zap className="w-5 h-5 text-brand-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-semibold text-brand-800 text-sm">AI Agents will run automatically</p>
              <p className="text-brand-600 text-xs mt-1 leading-relaxed">
                Business Understanding → Website Crawl → SEO Audit → Keyword Research → Content Gap Analysis → Content Generation → SEO Score → Full Report
              </p>
              <p className="text-slate-500 text-xs mt-2">Analysis typically takes 1–3 minutes depending on website size.</p>
            </div>
          </div>
        </div>

        <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 py-4 text-base">
          {loading
            ? <><Loader2 className="w-5 h-5 animate-spin" /> Launching AI Agents…</>
            : <><Zap className="w-5 h-5" /> Launch SEO Analysis</>}
        </button>
      </form>
    </div>
  )
}
