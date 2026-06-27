import Link from 'next/link'
import { Search, BarChart2, Zap, FileText, TrendingUp, Shield } from 'lucide-react'

const features = [
  { icon: Search, title: 'Smart Website Crawler', desc: 'Crawl and audit up to 10 pages automatically — detecting missing titles, broken tags, thin content, and more.' },
  { icon: BarChart2, title: 'AI Keyword Research', desc: 'Generate 30+ targeted keywords across 6 categories using Groq LLM — primary, long-tail, transactional, local and more.' },
  { icon: Zap, title: 'Content Gap Analysis', desc: 'Discover missing pages, topics, FAQs and landing pages by comparing your site against business requirements.' },
  { icon: FileText, title: 'Content Generation', desc: 'Auto-generate metadata, FAQs, blog ideas, CTAs, and schema suggestions tailored to your brand.' },
  { icon: TrendingUp, title: 'SEO Score & Report', desc: 'Get a detailed score across 4 dimensions and a complete PDF/JSON report with an actionable improvement plan.' },
  { icon: Shield, title: '100% Free Tools', desc: 'No paid SEO APIs required. Runs locally with FastAPI, LangGraph, Groq, SQLite and Next.js.' },
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 via-brand-700 to-indigo-600 text-white">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-5 max-w-7xl mx-auto">
        <div className="flex items-center gap-2 font-bold text-xl">
          <TrendingUp className="w-6 h-6 text-indigo-300" />
          SEO Growth AI
        </div>
        <div className="flex gap-3">
          <Link href="/login" className="px-4 py-2 rounded-xl border border-white/30 hover:bg-white/10 transition text-sm font-medium">Login</Link>
          <Link href="/register" className="px-4 py-2 rounded-xl bg-white text-brand-700 hover:bg-indigo-50 transition text-sm font-semibold">Get Started Free</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="text-center py-24 px-6 max-w-4xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur px-4 py-1.5 rounded-full text-sm mb-6 border border-white/20">
          <Zap className="w-4 h-4 text-yellow-300" /> Powered by LangGraph + Groq AI
        </div>
        <h1 className="text-5xl md:text-6xl font-extrabold mb-6 leading-tight">
          Your Autonomous<br />
          <span className="text-indigo-300">SEO Growth Agent</span>
        </h1>
        <p className="text-xl text-indigo-100 mb-10 max-w-2xl mx-auto leading-relaxed">
          Enter your business details. Our 8-agent AI pipeline crawls your site, finds SEO gaps, generates keywords, creates content and delivers a full report — in minutes.
        </p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link href="/register" className="bg-white text-brand-700 font-bold px-8 py-3.5 rounded-xl hover:bg-indigo-50 transition text-lg shadow-lg">
            Start Free Analysis →
          </Link>
          <Link href="/login" className="border border-white/40 px-8 py-3.5 rounded-xl hover:bg-white/10 transition text-lg font-semibold">
            Sign In
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="bg-white/5 backdrop-blur-sm py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">8 AI Agents Working For You</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <div key={i} className="bg-white/10 backdrop-blur rounded-2xl p-6 border border-white/10 hover:bg-white/15 transition">
                <f.icon className="w-8 h-8 text-indigo-300 mb-4" />
                <h3 className="font-bold text-lg mb-2">{f.title}</h3>
                <p className="text-indigo-200 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="text-center py-20 px-6">
        <h2 className="text-3xl font-bold mb-4">Ready to grow your SEO?</h2>
        <p className="text-indigo-200 mb-8">No credit card. No paid tools. Just AI-powered insights.</p>
        <Link href="/register" className="bg-white text-brand-700 font-bold px-10 py-4 rounded-xl hover:bg-indigo-50 transition text-lg shadow-xl">
          Create Free Account
        </Link>
      </section>

      <footer className="text-center py-8 text-indigo-300 text-sm border-t border-white/10">
        SEO Growth AI Agent — Built with FastAPI, LangGraph, Groq & Next.js
      </footer>
    </div>
  )
}
