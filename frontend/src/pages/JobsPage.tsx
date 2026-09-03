import { FormEvent, useEffect, useMemo, useState } from "react";
import { Alert, Button, MenuItem, TextField } from "@mui/material";
import type { GridColDef } from "@mui/x-data-grid";
import { createFieldJob, deleteFieldJob, updateFieldJob } from "../api/mutations";
import { errorMessage } from "../api/http";
import { listEquipment, listFieldJobs, optionalLookups } from "../api/resources";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { FormDialog } from "../components/FormDialog";
import { AddButton, ResourceGrid } from "../components/ResourceGrid";
import { RowActions } from "../components/RowActions";
import { StatusChip } from "../components/StatusChip";
import { useAuth } from "../context/AuthContext";
import { userName } from "../lookups";
import type { Equipment, FieldJob, JobPriority, JobStatus, User } from "../types";
import { JOB_PRIORITIES, JOB_STATUSES } from "../types";
import { JobReportsDialog } from "./JobReportsDialog";

type JobDraft = {
  title: string;
  priority: JobPriority;
  status: JobStatus;
  equipment_id: string;
  operator_id: string;
};

const emptyJob: JobDraft = {
  title: "",
  priority: "Medium",
  status: "Pending",
  equipment_id: "",
  operator_id: "",
};

export default function JobsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const isFieldHand = user?.role === "field_hand";
  const [rows, setRows] = useState<FieldJob[]>([]);
  const [equipment, setEquipment] = useState<Equipment[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<FieldJob | null>(null);
  const [draft, setDraft] = useState<JobDraft>(emptyJob);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<FieldJob | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [reportsJob, setReportsJob] = useState<FieldJob | null>(null);
  const [statusBusyId, setStatusBusyId] = useState<string | null>(null);

  const fieldHands = users.filter((person) => person.role === "field_hand");

  async function refresh() {
    const [jobs, units, lookups] = await Promise.all([listFieldJobs(), listEquipment(), optionalLookups()]);
    setRows(jobs);
    setEquipment(units);
    setUsers(lookups.users);
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    refresh()
      .catch((err) => {
        if (!cancelled) {
          setError(errorMessage(err, "Could not load field jobs."));
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

  function openCreate() {
    setEditing(null);
    setDraft({
      ...emptyJob,
      equipment_id: equipment[0]?.id ?? "",
      operator_id: fieldHands[0]?.id ?? "",
    });
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(job: FieldJob) {
    setEditing(job);
    setDraft({
      title: job.title,
      priority: job.priority,
      status: job.status,
      equipment_id: job.equipment_id,
      operator_id: job.operator_id,
    });
    setFormError(null);
    setFormOpen(true);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setFormError(null);
    const payload = {
      title: draft.title.trim(),
      priority: draft.priority,
      status: draft.status,
      equipment_id: draft.equipment_id,
      operator_id: draft.operator_id,
    };
    try {
      if (editing) {
        await updateFieldJob(editing.id, payload);
      } else {
        await createFieldJob(payload);
      }
      setFormOpen(false);
      await refresh();
    } catch (err) {
      setFormError(errorMessage(err, "Could not save field job."));
    } finally {
      setSubmitting(false);
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) {
      return;
    }
    setDeleting(true);
    try {
      await deleteFieldJob(pendingDelete.id);
      setPendingDelete(null);
      await refresh();
    } catch (err) {
      setError(errorMessage(err, "Could not delete field job."));
      setPendingDelete(null);
    } finally {
      setDeleting(false);
    }
  }

  async function changeStatus(job: FieldJob, status: JobStatus) {
    setStatusBusyId(job.id);
    setError(null);
    try {
      const updated = await updateFieldJob(job.id, { status });
      setRows((current) => current.map((row) => (row.id === updated.id ? updated : row)));
    } catch (err) {
      setError(errorMessage(err, "Could not update job status."));
    } finally {
      setStatusBusyId(null);
    }
  }

  const columns = useMemo<GridColDef[]>(
    () => [
      { field: "title", headerName: "Job", flex: 1.4, minWidth: 180 },
      {
        field: "priority",
        headerName: "Priority",
        width: 130,
        renderCell: (params) => <StatusChip kind="priority" value={params.value} />,
      },
      {
        field: "status",
        headerName: "Status",
        width: isFieldHand ? 170 : 150,
        renderCell: (params) =>
          isFieldHand ? (
            <TextField
              select
              size="small"
              value={params.row.status}
              disabled={statusBusyId === params.row.id}
              onChange={(event) => changeStatus(params.row, event.target.value as JobStatus)}
              sx={{ minWidth: 140 }}
            >
              {JOB_STATUSES.map((status) => (
                <MenuItem key={status} value={status}>
                  {status}
                </MenuItem>
              ))}
            </TextField>
          ) : (
            <StatusChip kind="job" value={params.value} />
          ),
      },
      {
        field: "equipment_id",
        headerName: "Equipment",
        flex: 1,
        minWidth: 140,
        valueGetter: (_value, row) => {
          const unit = equipment.find((item) => item.id === row.equipment_id);
          return unit ? `${unit.serial_number} (${unit.model})` : row.equipment_id.slice(0, 8);
        },
      },
      {
        field: "operator_id",
        headerName: "Operator",
        flex: 1,
        minWidth: 140,
        valueGetter: (_value, row) => userName(users, row.operator_id),
      },
      {
        field: "created_at",
        headerName: "Created",
        width: 160,
        valueFormatter: (value: string) => (value ? new Date(value).toLocaleString() : ""),
      },
      {
        field: "actions",
        headerName: "",
        width: isAdmin ? 200 : 140,
        sortable: false,
        filterable: false,
        renderCell: (params) => (
          <RowActions
            extra={
              <Button size="small" onClick={() => setReportsJob(params.row)}>
                Reports
              </Button>
            }
            onEdit={isAdmin ? () => openEdit(params.row) : undefined}
            onDelete={isAdmin ? () => setPendingDelete(params.row) : undefined}
          />
        ),
      },
    ],
    [equipment, isAdmin, isFieldHand, statusBusyId, users],
  );

  return (
    <>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <ResourceGrid
        title="Field Jobs"
        rows={rows}
        columns={columns}
        loading={loading}
        emptyLabel="No field jobs yet."
        headerAction={isAdmin ? <AddButton label="Add job" onClick={openCreate} /> : undefined}
      />
      <FormDialog
        open={formOpen}
        title={editing ? "Edit field job" : "Add field job"}
        error={formError}
        submitting={submitting}
        onClose={() => setFormOpen(false)}
        onSubmit={onSubmit}
      >
        <TextField
          label="Title"
          value={draft.title}
          onChange={(e) => setDraft({ ...draft, title: e.target.value })}
          required
          fullWidth
          margin="dense"
        />
        <TextField
          select
          label="Priority"
          value={draft.priority}
          onChange={(e) => setDraft({ ...draft, priority: e.target.value as JobPriority })}
          required
          fullWidth
          margin="dense"
        >
          {JOB_PRIORITIES.map((priority) => (
            <MenuItem key={priority} value={priority}>
              {priority}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          label="Status"
          value={draft.status}
          onChange={(e) => setDraft({ ...draft, status: e.target.value as JobStatus })}
          required
          fullWidth
          margin="dense"
        >
          {JOB_STATUSES.map((status) => (
            <MenuItem key={status} value={status}>
              {status}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          label="Equipment"
          value={draft.equipment_id}
          onChange={(e) => setDraft({ ...draft, equipment_id: e.target.value })}
          required
          fullWidth
          margin="dense"
        >
          {equipment.map((unit) => (
            <MenuItem key={unit.id} value={unit.id}>
              {unit.serial_number} ({unit.model})
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          label="Operator"
          value={draft.operator_id}
          onChange={(e) => setDraft({ ...draft, operator_id: e.target.value })}
          required
          fullWidth
          margin="dense"
        >
          {fieldHands.map((person) => (
            <MenuItem key={person.id} value={person.id}>
              {person.full_name}
            </MenuItem>
          ))}
        </TextField>
      </FormDialog>
      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Delete field job"
        body={pendingDelete ? `Delete “${pendingDelete.title}”? Service reports on this job will be removed.` : ""}
        onClose={() => setPendingDelete(null)}
        onConfirm={confirmDelete}
        busy={deleting}
      />
      <JobReportsDialog
        job={reportsJob}
        canUpload={Boolean(reportsJob && (isAdmin || isFieldHand))}
        onClose={() => setReportsJob(null)}
      />
    </>
  );
}
