import { FormEvent, useEffect, useMemo, useState } from "react";
import { Alert, MenuItem, TextField } from "@mui/material";
import type { GridColDef } from "@mui/x-data-grid";
import { createEquipment, deleteEquipment, updateEquipment } from "../api/mutations";
import { errorMessage } from "../api/http";
import { listEquipment, optionalLookups } from "../api/resources";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { FormDialog } from "../components/FormDialog";
import { AddButton, ResourceGrid } from "../components/ResourceGrid";
import { RowActions } from "../components/RowActions";
import { StatusChip } from "../components/StatusChip";
import { useAuth } from "../context/AuthContext";
import { farmName, userName } from "../lookups";
import type { Equipment, EquipmentStatus, Farm, User } from "../types";
import { EQUIPMENT_STATUSES } from "../types";

type EquipmentDraft = {
  serial_number: string;
  model: string;
  status: EquipmentStatus;
  fuel_level: string;
  facility_id: string;
  assigned_operator_id: string;
};

const emptyEquipment: EquipmentDraft = {
  serial_number: "",
  model: "",
  status: "Idle",
  fuel_level: "100",
  facility_id: "",
  assigned_operator_id: "",
};

export default function EquipmentPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [rows, setRows] = useState<Equipment[]>([]);
  const [farms, setFarms] = useState<Farm[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Equipment | null>(null);
  const [draft, setDraft] = useState<EquipmentDraft>(emptyEquipment);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Equipment | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fieldHands = users.filter((person) => person.role === "field_hand");

  async function refresh() {
    const [equipment, lookups] = await Promise.all([listEquipment(), optionalLookups()]);
    setRows(equipment);
    setFarms(lookups.farms);
    setUsers(lookups.users);
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    refresh()
      .catch((err) => {
        if (!cancelled) {
          setError(errorMessage(err, "Could not load equipment."));
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
    setDraft({ ...emptyEquipment, facility_id: farms[0]?.id ?? "" });
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(unit: Equipment) {
    setEditing(unit);
    setDraft({
      serial_number: unit.serial_number,
      model: unit.model,
      status: unit.status,
      fuel_level: String(unit.fuel_level),
      facility_id: unit.facility_id,
      assigned_operator_id: unit.assigned_operator_id ?? "",
    });
    setFormError(null);
    setFormOpen(true);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setFormError(null);
    const payload = {
      serial_number: draft.serial_number.trim(),
      model: draft.model.trim(),
      status: draft.status,
      fuel_level: Number(draft.fuel_level),
      facility_id: draft.facility_id,
      assigned_operator_id: draft.assigned_operator_id || null,
    };
    try {
      if (editing) {
        await updateEquipment(editing.id, payload);
      } else {
        await createEquipment(payload);
      }
      setFormOpen(false);
      await refresh();
    } catch (err) {
      setFormError(errorMessage(err, "Could not save equipment."));
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
      await deleteEquipment(pendingDelete.id);
      setPendingDelete(null);
      await refresh();
    } catch (err) {
      setError(errorMessage(err, "Could not delete equipment."));
      setPendingDelete(null);
    } finally {
      setDeleting(false);
    }
  }

  const columns = useMemo<GridColDef[]>(
    () => [
      { field: "serial_number", headerName: "Serial", flex: 1, minWidth: 140 },
      { field: "model", headerName: "Model", flex: 1, minWidth: 140 },
      {
        field: "status",
        headerName: "Status",
        width: 140,
        renderCell: (params) => <StatusChip kind="equipment" value={params.value} />,
      },
      { field: "fuel_level", headerName: "Fuel %", width: 110, type: "number" },
      {
        field: "facility_id",
        headerName: "Facility",
        flex: 1,
        minWidth: 140,
        valueGetter: (_value, row) => farmName(farms, row.facility_id),
      },
      {
        field: "assigned_operator_id",
        headerName: "Operator",
        flex: 1,
        minWidth: 140,
        valueGetter: (_value, row) => userName(users, row.assigned_operator_id),
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
    [farms, isAdmin, users],
  );

  return (
    <>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <ResourceGrid
        title="Equipment"
        rows={rows}
        columns={columns}
        loading={loading}
        emptyLabel="No equipment yet."
        headerAction={isAdmin ? <AddButton label="Add unit" onClick={openCreate} /> : undefined}
      />
      <FormDialog
        open={formOpen}
        title={editing ? "Edit equipment" : "Add equipment"}
        error={formError}
        submitting={submitting}
        onClose={() => setFormOpen(false)}
        onSubmit={onSubmit}
      >
        <TextField
          label="Serial number"
          value={draft.serial_number}
          onChange={(e) => setDraft({ ...draft, serial_number: e.target.value })}
          required
          fullWidth
          margin="dense"
        />
        <TextField
          label="Model"
          value={draft.model}
          onChange={(e) => setDraft({ ...draft, model: e.target.value })}
          required
          fullWidth
          margin="dense"
        />
        <TextField
          select
          label="Status"
          value={draft.status}
          onChange={(e) => setDraft({ ...draft, status: e.target.value as EquipmentStatus })}
          required
          fullWidth
          margin="dense"
        >
          {EQUIPMENT_STATUSES.map((status) => (
            <MenuItem key={status} value={status}>
              {status}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          label="Fuel %"
          type="number"
          value={draft.fuel_level}
          onChange={(e) => setDraft({ ...draft, fuel_level: e.target.value })}
          required
          fullWidth
          margin="dense"
          inputProps={{ min: 0, max: 100 }}
        />
        <TextField
          select
          label="Facility"
          value={draft.facility_id}
          onChange={(e) => setDraft({ ...draft, facility_id: e.target.value })}
          required
          fullWidth
          margin="dense"
        >
          {farms.map((farm) => (
            <MenuItem key={farm.id} value={farm.id}>
              {farm.name}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          label="Assigned operator"
          value={draft.assigned_operator_id}
          onChange={(e) => setDraft({ ...draft, assigned_operator_id: e.target.value })}
          fullWidth
          margin="dense"
        >
          <MenuItem value="">Unassigned</MenuItem>
          {fieldHands.map((person) => (
            <MenuItem key={person.id} value={person.id}>
              {person.full_name}
            </MenuItem>
          ))}
        </TextField>
      </FormDialog>
      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Delete equipment"
        body={pendingDelete ? `Delete ${pendingDelete.serial_number}? Units with field jobs cannot be removed.` : ""}
        onClose={() => setPendingDelete(null)}
        onConfirm={confirmDelete}
        busy={deleting}
      />
    </>
  );
}
