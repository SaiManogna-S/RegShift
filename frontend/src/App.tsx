import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Overview from './pages/Overview'
import Documents from './pages/Documents'
import ImpactAnalysis from './pages/ImpactAnalysis'
import ChangeTickets from './pages/ChangeTickets'
import AuditTrail from './pages/AuditTrail'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/overview" replace />} />
        <Route path="overview" element={<Overview />} />
        <Route path="documents" element={<Documents />} />
        <Route path="impact" element={<ImpactAnalysis />} />
        <Route path="tickets" element={<ChangeTickets />} />
        <Route path="audit" element={<AuditTrail />} />
      </Route>
    </Routes>
  )
}
