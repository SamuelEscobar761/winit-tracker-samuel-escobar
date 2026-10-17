import { useState, type FormEvent } from 'react'
import { KeyRound } from 'lucide-react'
import { ApiError } from '../../shared/api/http-client'
import { BrandMark } from '../../shared/ui/brand-mark'

interface LoginScreenProps {
  onLogin: (token: string) => Promise<void>
}

function describe(error: unknown): string {
  if (error instanceof ApiError && error.status === 429) return 'Too many attempts. Wait a minute and try again.'
  if (error instanceof ApiError && error.status === 401) return 'That token is not valid.'
  return 'Could not sign in. Check the connection.'
}

export function LoginScreen({ onLogin }: LoginScreenProps) {
  const [token, setToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isBusy, setIsBusy] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setIsBusy(true)
    setError(null)
    try {
      await onLogin(token)
    } catch (caught) {
      setError(describe(caught))
    } finally {
      setIsBusy(false)
    }
  }

  return (
    <div className="grid h-full place-items-center px-4">
      <form onSubmit={submit} className="w-full max-w-sm rounded-3xl bg-white p-8 shadow-card ring-1 ring-slate-200/70">
        <BrandMark />
        <h1 className="mt-6 text-xl font-bold text-slate-900">Sign in</h1>
        <p className="mt-1 text-sm text-slate-500">Live mode controls a real browser. Enter the access token.</p>
        <label className="mt-6 block text-xs font-medium text-slate-600">
          Access token
          <input
            type="password"
            autoComplete="current-password"
            autoFocus
            value={token}
            onChange={(event) => setToken(event.target.value)}
            className="mt-1 block w-full rounded-xl bg-slate-100 px-3 py-2 text-sm outline-none focus:bg-white focus:ring-2 focus:ring-indigo-300"
          />
        </label>
        {error && (
          <p role="alert" className="mt-3 text-xs text-rose-600">
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={!token || isBusy}
          className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-40"
        >
          <KeyRound size={15} /> Sign in
        </button>
      </form>
    </div>
  )
}
