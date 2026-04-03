import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import DashboardPage from './pages/DashboardPage'
import AdminPage from './pages/AdminPage'

function App() {
  const [appState, setAppState] = useState('landing')
  const [workerId, setWorkerId] = useState(null)
  const [enrollmentData, setEnrollmentData] = useState(null)
  const [formData, setFormData] = useState({ name: '', phone: '', vehicle: '', upi: '' })

  const handleEnrolled = (id, info, form) => {
    setWorkerId(id)
    setEnrollmentData(info)
    setFormData(form)
    setAppState('enrolled')
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={
          appState === 'landing'
            ? <LandingPage onEnrolled={handleEnrolled} />
            : <DashboardPage workerId={workerId} enrollmentData={enrollmentData} formData={formData} />
        } />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
