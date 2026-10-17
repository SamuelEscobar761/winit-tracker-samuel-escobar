import { useSyncExternalStore } from 'react'
import { parseRoute, type Route } from './hash-route'

function subscribe(onChange: () => void) {
  window.addEventListener('hashchange', onChange)
  return () => window.removeEventListener('hashchange', onChange)
}

const readHash = () => window.location.hash

export function useHashRoute(): Route {
  const hash = useSyncExternalStore(subscribe, readHash)
  return parseRoute(hash)
}

export function navigate(hash: string) {
  window.location.hash = hash
}
