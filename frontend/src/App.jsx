// src/App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AthleteProvider } from './context/AthleteContext';
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
    <AthleteProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="profile" element={<Profile />} />
            <Route path="readiness" element={<Readiness />} />
            <Route path="heatmap" element={<Heatmap />} />
            <Route path="workout" element={<WorkoutLog />} />
            <Route path="acwr" element={<ACWRMonitor />} />
            <Route path="recovery" element={<Recovery />} />
            <Route path="records" element={<AthleteRecords />} />
            <Route path="wearable" element={<WearableSync />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AthleteProvider>
  );
}
