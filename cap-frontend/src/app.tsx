import { JobPage } from './features/job/job-page'
import { StandaloneView } from './features/scraper/standalone-view'
import { RulesScreen } from './features/rules/rules-screen'
import { LoginScreen } from './features/session/login-screen'
import { usePublicConfig } from './features/session/use-public-config'
import { useSession } from './features/session/use-session'
import { UploadScreen } from './features/upload/upload-screen'
import { useHashRoute } from './shared/routing/use-hash-route'
import { EmptyState } from './shared/ui/empty-state'
import { WifiOff } from 'lucide-react'

export default function App() {
  const route = useHashRoute()
  const session = useSession()
  const isSignedIn =
    session.state.status === 'ready' &&
    (!session.state.info.authentication_required || session.state.info.authenticated)
  const config = usePublicConfig(isSignedIn)

  if (session.state.status === 'loading') {
    return <div className="grid h-full place-items-center text-sm text-slate-400">Loading…</div>
  }
  if (session.state.status === 'error') {
    return (
      <div className="grid h-full place-items-center">
        <EmptyState tone="red" icon={<WifiOff size={20} />} title="The server is not reachable" hint={session.state.message} />
      </div>
    )
  }
  if (!isSignedIn) return <LoginScreen onLogin={session.login} />

  const onSignOut = session.state.info.authentication_required ? () => void session.logout() : null
  if (route.name === 'job') {
    return <JobPage key={route.jobId} jobId={route.jobId} provider={config?.provider ?? null} onSignOut={onSignOut} />
  }
  if (route.name === 'rules') return <RulesScreen />
  if (route.name === 'live') return <StandaloneView lane={route.lane} />
  return <UploadScreen config={config} onSignOut={onSignOut} />
}
