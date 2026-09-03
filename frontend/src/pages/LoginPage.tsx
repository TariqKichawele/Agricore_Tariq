import { FormEvent, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { Agriculture } from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import axios from "axios";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { user, loading, login } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState("admin@agricore.local");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <Typography color="text.secondary">Restoring session…</Typography>
      </Box>
    );
  }

  if (user) {
    const from = (location.state as { from?: string } | null)?.from;
    return <Navigate to={from && from !== "/login" ? from : "/"} replace />;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        setError("Incorrect email or password.");
      } else {
        setError("Could not reach the API. Is the backend running?");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "background.default",
        p: 2,
      }}
    >
      <Paper sx={{ p: 4, width: "100%", maxWidth: 420 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1 }}>
          <Agriculture color="primary" fontSize="large" />
          <Typography variant="h5">AgriCore</Typography>
        </Box>
        <Typography color="text.secondary" sx={{ mb: 3 }}>
          Prairie Crest Agricultural Cooperative — sign in to the Command Center.
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <Box component="form" onSubmit={onSubmit}>
          <TextField
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            fullWidth
            required
            autoComplete="username"
            margin="normal"
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
            required
            autoComplete="current-password"
            margin="normal"
          />
          <Button type="submit" variant="contained" fullWidth size="large" sx={{ mt: 2 }} disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
