import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './mockup.css'
import MockupApp from './MockupApp'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MockupApp />
  </StrictMode>,
)
