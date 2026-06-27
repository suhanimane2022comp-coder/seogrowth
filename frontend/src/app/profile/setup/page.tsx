'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { TrendingUp, Loader2, CheckCircle2 } from 'lucide-react'
import { getProfile, saveProfile } from '@/lib/api'

const BUSINESS_TYPES = ['Ecommerce', 'Service', 'Local Business', 'SaaS', 'Blog', 'Agency', 'Healthcare', 'Education', 'Others']
const BRAND_TONES = ['Professional', 'Friendly', 'Luxury', 'Minimal', 'Playful']
const PLATFORMS = ['Instagram', 'Facebook', 'LinkedIn', 'Pinterest', 'X', 'YouTube', 'Threads']

export default function ProfileSetupPage() {
  const router = useRouter()
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [isEdit, setIsEdit] = useState(false)

  const [form, setForm] = useState({
    business_name: '',
    industry: '',
    business_type: 'Ecommerce',
    website_url: '',
    business_description: '',
    products_services: '',
    target_location: '',
    languages: '',
    keywords: '',
    brand_tone: 'Professional',
  })
  const [socialLinks, setSocialLinks] = useState<Record<string, string>>({})

  useEffect(() => {
    getProfile()
      .then((res) => {
        const p = res.data
        setIsEdit(true)
        setForm({
          business_name: p.business_name || '',
          industry: p.industry || '',
          business_type: p.business_type || 'Ecommerce',
          website_url: p.website_url || '',
          business_description: p.business_description || '',
          products_services: p.products_services || '',
          target_location: p.target_location || '',
          languages: (p.languages || []).join(', '),
          keywords: (p.keywords || []).join(', '),
          brand_tone: p.brand_tone || 'Professional',
        })
        setSocialLinks(p.social_media_links || {})
      })
      .catch(() => {})
      .finally(() => setLoadingProfile(false))
  }, [])

  const set = (key: string, value: string) => setForm((p) => ({ ...p, [key]: value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      const payload = {
        ...form,
        languages: form.languages.split(',').map((s) => s.trim()).filter(Boolean),
        keywords: form.keywords.split(',').map((s) => s.trim()).filter(Boolean),
        social_media_links: Object.fromEntries(Object.entries(socialLinks).filter(([, v]) => v)),
      }
      await saveProfile(payload)
      setSuccess(true)
      setTimeout(() => router.push('/dashboard'), 1200)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save profile')
    } finally {
      setSaving(false)
    }
  }

  if (loadingProfile) {
    return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-brand-600" /></div>
  }

  return (
    <div>
      <div className="text-center mb-8">
        <div className="flex justify-center mb-3">
          <div className="bg-brand-600 p-3 rounded-2xl"><TrendingUp className="w-7 h-7 text-white" /></div>
        </div>
        <h1 className="text-2xl font-bold text-slate-800">{isEdit ? 'Update Your Business Profile' : 'Set Up Your Business Profile'}</h1>
        <p className="text-slate-500 text-sm mt-1">
          We use this to auto-generate your target audience, competitors, and tailored SEO &amp; social media strategy.
        </p>
      </div>

      {error && <div className="bg-red-50 text-red-600 text-sm rounded-xl px-4 py-3 mb-4">{error}</div>}
      {success && (
        <div className="bg-emerald-50 text-emerald-700 text-sm rounded-xl px-4 py-3 mb-4 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> Profile saved! Generating audience persona &amp; competitors...
        </div>
      )}

      <form onSubmit={handleSubmit} className="card space-y-6">
        <div>
          <h2 className="font-semibold text-slate-800 mb-3">Business Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Business Name</label>
              <input className="input" required value={form.business_name} onChange={(e) => set('business_name', e.target.value)} />
            </div>
            <div>
              <label className="label">Industry / Niche</label>
              <input className="input" required placeholder="e.g. Skincare, Fitness, SaaS" value={form.industry} onChange={(e) => set('industry', e.target.value)} />
            </div>
            <div>
              <label className="label">Business Type</label>
              <select className="input" value={form.business_type} onChange={(e) => set('business_type', e.target.value)}>
                {BUSINESS_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Website URL</label>
              <input className="input" placeholder="https://example.com" value={form.website_url} onChange={(e) => set('website_url', e.target.value)} />
            </div>
            <div>
              <label className="label">Target Location</label>
              <input className="input" required placeholder="e.g. India, Mumbai, Global" value={form.target_location} onChange={(e) => set('target_location', e.target.value)} />
            </div>
            <div>
              <label className="label">Brand Tone</label>
              <select className="input" value={form.brand_tone} onChange={(e) => set('brand_tone', e.target.value)}>
                {BRAND_TONES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>

          <div className="mt-4">
            <label className="label">Business Description</label>
            <textarea className="input" rows={3} required value={form.business_description} onChange={(e) => set('business_description', e.target.value)} />
          </div>
          <div className="mt-4">
            <label className="label">Products / Services</label>
            <textarea className="input" rows={3} required value={form.products_services} onChange={(e) => set('products_services', e.target.value)} />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div>
              <label className="label">Languages (comma separated)</label>
              <input className="input" placeholder="English, Hindi" value={form.languages} onChange={(e) => set('languages', e.target.value)} />
            </div>
            <div>
              <label className="label">Keywords (comma separated)</label>
              <input className="input" placeholder="organic skincare, vegan cosmetics" value={form.keywords} onChange={(e) => set('keywords', e.target.value)} />
            </div>
          </div>
        </div>

        <div>
          <h2 className="font-semibold text-slate-800 mb-3">Social Media Links</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {PLATFORMS.map((p) => (
              <div key={p}>
                <label className="label">{p}</label>
                <input
                  className="input"
                  placeholder={`https://${p.toLowerCase()}.com/yourbrand`}
                  value={socialLinks[p] || ''}
                  onChange={(e) => setSocialLinks((prev) => ({ ...prev, [p]: e.target.value }))}
                />
              </div>
            ))}
          </div>
        </div>

        <button type="submit" disabled={saving} className="btn-primary w-full flex items-center justify-center gap-2">
          {saving ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving &amp; generating insights...</> : isEdit ? 'Update Profile' : 'Save & Continue'}
        </button>
      </form>
    </div>
  )
}
