import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import PipelineBuilder from "./pages/PipelineBuilder";
import ExecutionMonitor from "./pages/ExecutionMonitor";
import PipelineHistory from "./pages/PipelineHistory";
import ScheduledPipelines from "./pages/ScheduledPipelines";

export default function App() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        {/* Public */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/build" element={<ProtectedRoute><PipelineBuilder /></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute><PipelineHistory /></ProtectedRoute>} />
        <Route path="/schedules" element={<ProtectedRoute><ScheduledPipelines /></ProtectedRoute>} />
        <Route path="/executions/:executionId" element={<ProtectedRoute><ExecutionMonitor /></ProtectedRoute>} />
      </Routes>
    </AnimatePresence>
  );
}
