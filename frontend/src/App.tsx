import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import OverviewPage from './pages/OverviewPage';
import DataPage from './pages/DataPage';
import PredictPage from './pages/PredictPage';
import OptimizePage from './pages/OptimizePage';
import PlanPage from './pages/PlanPage';
import LivePage from './pages/LivePage';
import ScenarioPage from './pages/ScenarioPage';
import ComparePage from './pages/ComparePage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<OverviewPage />} />
          <Route path="data" element={<DataPage />} />
          <Route path="predict" element={<PredictPage />} />
          <Route path="optimize" element={<OptimizePage />} />
          <Route path="plan" element={<PlanPage />} />
          <Route path="live" element={<LivePage />} />
          <Route path="scenario" element={<ScenarioPage />} />
          <Route path="compare" element={<ComparePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
