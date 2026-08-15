import { useEffect } from 'react'
import { Header } from './components/layout/Header'
import { LeftSidebar } from './components/layout/LeftSidebar'
import { RightPanel } from './components/layout/RightPanel'
import { GraphCanvas } from './components/experiment/GraphCanvas'
import { ExperimentModal } from './components/experiment/ExperimentModal'
import { fetchExperimentHistory, fetchSystems } from './services/api'
import { useStore } from './store/experimentStore'

export default function App() {
  const { system, setSystem, setExperimentHistory } = useStore()

  useEffect(() => {
    async function restoreWorkspace() {
      try {
        const savedSystems = await fetchSystems()
        const savedSystem = savedSystems.find((item) => item.id === system.id)
        if (savedSystem) setSystem(savedSystem)

        const history = await fetchExperimentHistory(savedSystem?.id ?? system.id)
        setExperimentHistory(history)
      } catch {
        // The dashboard remains usable when the backend is offline.
      }
    }

    void restoreWorkspace()
  }, [setExperimentHistory, setSystem, system.id])

  return (
    <div className="app-shell">
      <Header />
      <LeftSidebar />
      <GraphCanvas />
      <RightPanel />
      <ExperimentModal />
    </div>
  )
}
