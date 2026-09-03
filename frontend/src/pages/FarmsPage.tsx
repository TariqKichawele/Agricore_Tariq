import { FormEvent, useEffect, useMemo, useState } from "react";
import { Alert, MenuItem, TextField } from "@mui/material";
import type { GridColDef } from "@mui/x-data-grid";
import { createFarm, deleteFarm, updateFarm } from "../api/mutations";
import { errorMessage } from "../api/http";
import { listFarms, listUsers } from "../api/resources";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { FormDialog } from "../components/FormDialog";
import { AddButton, ResourceGrid } from "../components/ResourceGrid";
import { RowActions } from "../components/RowActions";
import { useAuth } from "../context/AuthContext";
import { userName } from "../lookups";
import type { Farm, User } from "../types";

type FarmDraft = {
  name: string;
  location_region: string;
  capacity: string;
  supervisor_id: string;
};

const emptyFarm: FarmDraft = { name: "", location_region: "", capacity: "0", supervisor_id: "" };

export default function FarmsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [rows, setRows] = useState<Farm[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Farm | null>(null);
  const [draft, setDraft] = useState<FarmDraft>(emptyFarm);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Farm | null>(null);
  const [deleting, setDeleting] = useState(false);

  async function refresh() {
    const [farms, people] = await Promise.all([listFarms(), listUsers()]);
    setRows(farms);
    setUsers(people);
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    refresh()
      .catch((err) => {
        if (!cancelled) {
          setError(errorMessage(err, "Could not load farms."));
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
    setDraft(emptyFarm);
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(farm: Farm) {
    setEditing(farm);
    setDraft({
      name: farm.name,
      location_region: farm.location_region,
      capacity: String(farm.capacity),
      supervisor_id: farm.supervisor_id ?? "",
    });
    setFormError(null);
    setFormOpen(true);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setFormError(null);
    const payload = {
      name: draft.name.trim(),
      location_region: draft.location_region.trim(),
      capacity: Number(draft.capacity),
      supervisor_id: draft.supervisor_id || null,
    };
    try {
      if (editing) {
        await updateFarm(editing.id, payload);
      } else {
        await createFarm(payload);
      }
      setFormOpen(false);
      await refresh();
    } catch (err) {
      setFormError(errorMessage(err, "Could not save farm."));
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
      await deleteFarm(pendingDelete.id);
      setPendingDelete(null);
      await refresh();
    } catch (err) {
      setError(errorMessage(err, "Could not delete farm."));
      setPendingDelete(null);
    } finally {
      setDeleting(false);
    }
  }

  const columns = useMemo<GridColDef[]>(
    () => [
      { field: "name", headerName: "Farm", flex: 1.2, minWidth: 160 },
      { field: "location_region", headerName: "Region", flex: 1, minWidth: 140 },
      { field: "capacity", headerName: "Capacity", width: 120, type: "number" },
      {
        field: "supervisor_id",
        headerName: "Supervisor",
        flex: 1,
        minWidth: 140,
        valueGetter: (_value, row) => userName(users, row.supervisor_id),
      },
      ...(isAdmin
        ? [
            {
              field: "actions",
              headerName: "",
              width: 110,
              sortable: false,
              filterable: false,
              renderCell: (params) => (
                <RowActions onEdit={() => openEdit(params.row)} onDelete={() => setPendingDelete(params.row)} />
              ),
            } satisfies GridColDef,
          ]
        : []),
    ],
    [isAdmin, users],
  );

  return (
    <>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <ResourceGrid
        title="Farms"
        rows={rows}
        columns={columns}
        loading={loading}
        emptyLabel="No farms yet."
        headerAction={isAdmin ? <AddButton label="Add farm" onClick={openCreate} /> : undefined}
      />
      <FormDialog
        open={formOpen}
        title={editing ? "Edit farm" : "Add farm"}
        error={formError}
        submitting={submitting}
        onClose={() => setFormOpen(false)}
        onSubmit={onSubmit}
      >
        <TextField
          label="Name"
          value={draft.name}
          onChange={(e) => setDraft({ ...draft, name: e.target.value })}
          required
          fullWidth
          margin="dense"
        />
        <TextField
          label="Region"
          value={draft.location_region}
          onChange={(e) => setDraft({ ...draft, location_region: e.target.value })}
          required
          fullWidth
          margin="dense"
        />
        <TextField
          label="Capacity"
          type="number"
          value={draft.capacity}
          onChange={(e) => setDraft({ ...draft, capacity: e.target.value })}
          required
          fullWidth
          margin="dense"
          inputProps={{ min: 0 }}
        />
        <TextField
          select
          label="Supervisor"
          value={draft.supervisor_id}
          onChange={(e) => setDraft({ ...draft, supervisor_id: e.target.value })}
          fullWidth
          margin="dense"
        >
          <MenuItem value="">None</MenuItem>
          {users.map((person) => (
            <MenuItem key={person.id} value={person.id}>
              {person.full_name}
            </MenuItem>
          ))}
        </TextField>
      </FormDialog>
      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Delete farm"
        body={pendingDelete ? `Delete ${pendingDelete.name}? Equipment still assigned to this site cannot be left behind.` : ""}
        onClose={() => setPendingDelete(null)}
        onConfirm={confirmDelete}
        busy={deleting}
      />
    </>
  );
}
