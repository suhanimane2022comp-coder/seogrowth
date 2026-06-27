'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import { getProfile } from '@/lib/api'
import { Loader2 } from 'lucide-react'

export default function AnalyzeLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    getProfile()
      .then(() => setChecking(false))
      .catch((err) => {
        if (err.response?.status === 404) {
          router.replace('/profile/setup')
        } else {
          setChecking(false)
        }
      })
  }, [router])

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto">{children}</main>
    </div>
  )
}
