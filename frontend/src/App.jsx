import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AthleteProvider } from './context/AthleteContext';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import Readiness from './pages/Readiness';
import Heatmap from './pages/Heatmap';
import WorkoutLog from './pages/WorkoutLog';
import ACWRMonitor from './pages/ACWRMonitor';
import Recovery from './pages/Recovery';
import WearableSync from './pages/WearableSync';
import AthleteRecords from './pages/AthleteRecords';

export default function App() {
  return (
    <AuthProvider>
      <AthleteProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />

            <Route path="/" element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }>
              <Route index element={<Dashboard />} />
              <Route path="profile" element={<Profile />} />
              <Route path="readiness" element={<Readiness />} />
              <Route path="heatmap" element={<Heatmap />} />
              <Route path="workout" element={<WorkoutLog />} />
              <Route path="acwr" element={<ACWRMonitor />} />
              <Route path="recovery" element={<Recovery />} />
              <Route path="wearable" element={<WearableSync />} />

              <Route path="records" element={
                <ProtectedRoute allowedRoles={['Coach', 'Medical Staff', 'Admin']}>
                  <AthleteRecords />
                </ProtectedRoute>
              } />
            </Route>
          </Routes>
        </BrowserRouter>
      </AthleteProvider>
    </AuthProvider>
  );
}

