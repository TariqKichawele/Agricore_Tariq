import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import {
  fetchCoLocation,
  fetchLowFuel,
  fetchMaintenanceFlags,
  fetchReliability,
  fetchReportingLines,
  optionalLookups,
} from "../api/resources";
import { errorMessage } from "../api/http";
import { useAuth } from "../context/AuthContext";
import { supervisorsFromFarms } from "../lookups";
import type {
  CoLocationResponse,
  LowFuelResponse,
  MaintenanceFlagsResponse,
  ReliabilityResponse,
  ReportingLinesResponse,
  User,
} from "../types";

type MetricCardProps = {
  title: string;
  value: string;
  detail: string;
  tone?: "default" | "warn";
};

function MetricCard({ title, value, detail, tone = "default" }: MetricCardProps) {
  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Typography variant="overline" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h4" color={tone === "warn" && value !== "0" ? "warning.main" : "text.primary"}>
          {value}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {detail}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lowFuel, setLowFuel] = useState<LowFuelResponse | null>(null);
  const [coLocation, setCoLocation] = useState<CoLocationResponse | null>(null);
  const [reliability, setReliability] = useState<ReliabilityResponse | null>(null);
  const [maintenance, setMaintenance] = useState<MaintenanceFlagsResponse | null>(null);
  const [supervisors, setSupervisors] = useState<User[]>([]);
  const [supervisorId, setSupervisorId] = useState("");
  const [reporting, setReporting] = useState<ReportingLinesResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      fetchLowFuel(),
      fetchCoLocation(),
      fetchReliability(),
      fetchMaintenanceFlags(),
      optionalLookups(),
    ])
      .then(([fuel, coloc, rel, maint, lookups]) => {
        if (cancelled) {
          return;
        }
        setLowFuel(fuel);
        setCoLocation(coloc);
        setReliability(rel);
        setMaintenance(maint);
        const nextSupervisors = supervisorsFromFarms(lookups.farms, lookups.users);
        setSupervisors(nextSupervisors);
        setSupervisorId((current) => current || nextSupervisors[0]?.id || "");
      })
      .catch((err) => {
        if (!cancelled) {
          setError(errorMessage(err, "Could not load analytics."));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!supervisorId) {
      setReporting(null);
      return;
    }
    let cancelled = false;
    fetchReportingLines(supervisorId)
      .then((data) => {
        if (!cancelled) {
          setReporting(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setReporting({ count: 0, field_hands: [] });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [supervisorId]);

  const reliabilitySummary = useMemo(() => {
    const models = reliability?.models ?? [];
    const completed = models.reduce((sum, row) => sum + row.completed, 0);
    const failed = models.reduce((sum, row) => sum + row.failed, 0);
    return { models: models.length, completed, failed };
  }, [reliability]);

  const lowFuelHint = lowFuel?.items[0]
    ? `Lowest: ${lowFuel.items[0].serial_number} at ${lowFuel.items[0].fuel_level}%`
    : "Active units (Idle / In-Use) below 20% fuel";

  const canPickSupervisor = user?.role === "admin" || user?.role === "auditor";

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Stack spacing={3}>
      {error && <Alert severity="error">{error}</Alert>}
      <Box
        sx={{
          display: "grid",
          gap: 2,
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        }}
      >
        <MetricCard title="Low fuel" value={String(lowFuel?.count ?? "—")} detail={lowFuelHint} tone="warn" />
        <MetricCard
          title="Co-location mismatches"
          value={String(coLocation?.count ?? "—")}
          detail="Assigned operator farm differs from equipment facility"
          tone="warn"
        />
        <MetricCard
          title="Model reliability"
          value={`${reliabilitySummary.completed}/${reliabilitySummary.failed}`}
          detail={`${reliabilitySummary.models} models — completed / failed jobs`}
        />
        <MetricCard
          title="Maintenance flags"
          value={String(maintenance?.count ?? "—")}
          detail="Farms where maintenance units are more than 30% of the fleet"
          tone="warn"
        />
        <MetricCard
          title="Active reporting lines"
          value={supervisorId ? String(reporting?.count ?? "—") : "—"}
          detail="Field hands on this supervisor’s farms with Pending or In-Progress jobs"
        />
      </Box>

      {canPickSupervisor && (
        <FormControl size="small" sx={{ maxWidth: 360 }}>
          <InputLabel id="supervisor-label">Reporting-line supervisor</InputLabel>
          <Select
            labelId="supervisor-label"
            label="Reporting-line supervisor"
            value={supervisorId}
            onChange={(event) => setSupervisorId(event.target.value)}
          >
            {supervisors.length === 0 && (
              <MenuItem value="" disabled>
                No farm supervisors yet
              </MenuItem>
            )}
            {supervisors.map((supervisor) => (
              <MenuItem key={supervisor.id} value={supervisor.id}>
                {supervisor.full_name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}

      {reliability && reliability.models.length > 0 && (
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Jobs by model
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {reliability.models
              .map((row) => `${row.model}: ${row.completed} completed, ${row.failed} failed`)
              .join(" · ")}
          </Typography>
        </Box>
      )}
    </Stack>
  );
}
