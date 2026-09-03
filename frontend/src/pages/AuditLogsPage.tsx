import { FormEvent, useEffect, useMemo, useState } from "react";
import { Alert, Box, Button, TextField } from "@mui/material";
import type { GridColDef } from "@mui/x-data-grid";
import { listAuditLogs } from "../api/mutations";
import { errorMessage } from "../api/http";
import { optionalLookups } from "../api/resources";
import { ResourceGrid } from "../components/ResourceGrid";
import { userName } from "../lookups";
import type { AuditLog, User } from "../types";

export default function AuditLogsPage() {
  const [query, setQuery] = useState("");
  const [applied, setApplied] = useState("");
  const [rows, setRows] = useState<AuditLog[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([listAuditLogs(applied), optionalLookups()])
      .then(([logs, lookups]) => {
        if (cancelled) {
          return;
        }
        setRows(logs);
        setUsers(lookups.users);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(errorMessage(err, "Could not load audit logs."));
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
  }, [applied]);

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setApplied(query);
  }

  const columns = useMemo<GridColDef[]>(
    () => [
      {
        field: "created_at",
        headerName: "When",
        width: 180,
        valueFormatter: (value: string) => (value ? new Date(value).toLocaleString() : ""),
      },
      {
        field: "actor_id",
        headerName: "Actor",
        flex: 1,
        minWidth: 140,
        valueGetter: (_value, row) => (row.actor_id ? userName(users, row.actor_id) : "System"),
      },
      { field: "action", headerName: "Action", width: 110 },
      { field: "entity_type", headerName: "Entity", width: 140 },
      {
        field: "entity_id",
        headerName: "Entity ID",
        width: 140,
        valueGetter: (_value, row) => row.entity_id?.slice(0, 8) ?? "—",
      },
      {
        field: "details",
        headerName: "Details",
        flex: 1.4,
        minWidth: 200,
        valueGetter: (_value, row) => (row.details ? JSON.stringify(row.details) : ""),
      },
    ],
    [users],
  );

  return (
    <>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <Box component="form" onSubmit={onSearch} sx={{ display: "flex", gap: 1, mb: 2, maxWidth: 560 }}>
        <TextField
          label="Search action, entity, or details"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          size="small"
          fullWidth
        />
        <Button type="submit" variant="contained">
          Search
        </Button>
        <Button
          type="button"
          onClick={() => {
            setQuery("");
            setApplied("");
          }}
        >
          Clear
        </Button>
      </Box>
      <ResourceGrid
        title="Audit Logs"
        rows={rows}
        columns={columns}
        loading={loading}
        emptyLabel="No matching log entries."
      />
    </>
  );
}
