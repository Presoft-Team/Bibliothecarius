import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { initKeycloak } from './lib/keycloak'

const root = createRoot(document.getElementById('root')!)

initKeycloak()
  .then((authenticated) => {
    if (!authenticated) {
      root.render(
        <p className="p-8 text-slate-600 dark:text-slate-300">
          Authentication failed. Please refresh to try again.
        </p>,
      )
      return
    }
    root.render(
      <StrictMode>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </StrictMode>,
    )
  })
  .catch(() => {
    root.render(
      <p className="p-8 text-slate-600 dark:text-slate-300">
        Could not reach the authentication server. Please refresh to try again.
      </p>,
    )
  })
