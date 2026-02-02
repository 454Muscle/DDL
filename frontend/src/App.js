import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import { Header } from "./components/Header";
import HomePage from "./pages/HomePage";
import SubmitPage from "./pages/SubmitPage";
import AuthPage from "./pages/AuthPage";
import AdminLoginPage from "./pages/AdminLoginPage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import AdminForgotPasswordPage from "./pages/AdminForgotPasswordPage";
import AdminResetPasswordPage from "./pages/AdminResetPasswordPage";

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <div className="app-container">
                    <BrowserRouter>
                        <Header />
                        <Routes>
                            <Route path="/" element={<HomePage />} />
                            <Route path="/submit" element={<SubmitPage />} />
                            <Route path="/auth" element={<AuthPage />} />
                            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                            <Route path="/reset-password" element={<ResetPasswordPage />} />
                            <Route path="/admin" element={<AdminLoginPage />} />
                            <Route path="/admin/forgot-password" element={<AdminForgotPasswordPage />} />
                            <Route path="/admin/reset-password" element={<AdminResetPasswordPage />} />
                            <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
                        </Routes>
                    </BrowserRouter>
                    <Toaster 
                        position="top-right"
                        toastOptions={{
                            style: {
                                background: 'hsl(var(--card))',
                                color: 'hsl(var(--foreground))',
                                border: '1px solid hsl(var(--border))',
                                fontFamily: "'JetBrains Mono', monospace"
                            }
                        }}
                    />
                </div>
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App;
