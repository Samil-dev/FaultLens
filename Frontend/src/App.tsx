import { Header } from './components/layout/Header'
import { LeftSidebar } from './components/layout/LeftSidebar'
import { RightPanel } from './components/layout/RightPanel'
import { GraphCanvas } from './components/experiment/GraphCanvas'
import { ExperimentModal } from './components/experiment/ExperimentModal'

export default function App() {
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
