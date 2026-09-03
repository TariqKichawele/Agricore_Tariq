import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import AuditLogsPage from "./pages/AuditLogsPage";
import DashboardPage from "./pages/DashboardPage";
import EquipmentPage from "./pages/EquipmentPage";
import FarmsPage from "./pages/FarmsPage";
import JobsPage from "./pages/JobsPage";
import LoginPage from "./pages/LoginPage";
import UsersPage from "./pages/UsersPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/farms" element={<FarmsPage />} />
            <Route path="/equipment" element={<EquipmentPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/users" element={<UsersPage />} />
            <Route path="/audit-logs" element={<AuditLogsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
