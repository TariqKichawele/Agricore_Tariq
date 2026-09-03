import { FormEvent, useEffect, useMemo, useState } from "react";
import { Alert, FormControlLabel, MenuItem, Switch, TextField } from "@mui/material";
import type { GridColDef } from "@mui/x-data-grid";
import { createUser, deleteUser, updateUser } from "../api/mutations";
import { errorMessage } from "../api/http";
import { listFarms, listUsers } from "../api/resources";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { FormDialog } from "../components/FormDialog";
import { AddButton, ResourceGrid } from "../components/ResourceGrid";
import { RowActions } from "../components/RowActions";
import { useAuth } from "../context/AuthContext";
import { farmName } from "../lookups";
import { ROLE_LABEL } from "../nav";
import type { Farm, User, UserRole } from "../types";
import { USER_ROLES } from "../types";

type UserDraft = {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
  farm_id: string;
  is_active: boolean;
};

const emptyUser: UserDraft = {
  email: "",
  password: "",
  full_name: "",
  role: "field_hand",
  farm_id: "",
  is_active: true,
};

export default function UsersPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [rows, setRows] = useState<User[]>([]);
  const [farms, setFarms] = useState<Farm[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [draft, setDraft] = useState<UserDraft>(emptyUser);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<User | null>(null);
  const [deleting, setDeleting] = useState(false);

  async function refresh() {
    const [people, sites] = await Promise.all([listUsers(), listFarms()]);
    setRows(people);
    setFarms(sites);
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    refresh()
      .catch((err) => {
        if (!cancelled) {
          setError(errorMessage(err, "Could not load users."));
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
    setDraft(emptyUser);
    setFormError(null);
    setFormOpen(true);
  }

  function openEdit(person: User) {
    setEditing(person);
    setDraft({
      email: person.email,
      password: "",
      full_name: person.full_name,
      role: person.role,
      farm_id: person.farm_id ?? "",
      is_active: person.is_active,
    });
    setFormError(null);
    setFormOpen(true);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      if (editing) {
        const payload: Parameters<typeof updateUser>[1] = {
          email: draft.email.trim(),
          full_name: draft.full_name.trim(),
          role: draft.role,
          farm_id: draft.farm_id || null,
          is_active: draft.is_active,
        };
        if (draft.password.trim()) {
          payload.password = draft.password;
        }
        await updateUser(editing.id, payload);
      } else {
        await createUser({
          email: draft.email.trim(),
          password: draft.password,
          full_name: draft.full_name.trim(),
          role: draft.role,
          farm_id: draft.farm_id || null,
          is_active: draft.is_active,
        });
      }
      setFormOpen(false);
      await refresh();
    } catch (err) {
      setFormError(errorMessage(err, "Could not save user."));
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
      await deleteUser(pendingDelete.id);
      setPendingDelete(null);
      await refresh();
    } catch (err) {
      setError(errorMessage(err, "Could not delete user."));
      setPendingDelete(null);
    } finally {
      setDeleting(false);
    }
  }

  const columns = useMemo<GridColDef[]>(
    () => [
      { field: "full_name", headerName: "Name", flex: 1, minWidth: 140 },
      { field: "email", headerName: "Email", flex: 1.2, minWidth: 180 },
      {
        field: "role",
        headerName: "Role",
        width: 180,
        valueGetter: (_value, row) => ROLE_LABEL[row.role as UserRole],
      },
      {
        field: "farm_id",
        headerName: "Home farm",
        flex: 1,
        minWidth: 140,
        valueGetter: (_value, row) => (row.farm_id ? farmName(farms, row.farm_id) : "—"),
      },
      {
        field: "is_active",
        headerName: "Active",
        width: 100,
        valueGetter: (_value, row) => (row.is_active ? "Yes" : "No"),
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
                <RowActions
                  onEdit={() => openEdit(params.row)}
                  onDelete={params.row.id === user?.id ? undefined : () => setPendingDelete(params.row)}
                />
              ),
            } satisfies GridColDef,
          ]
        : []),
    ],
    [farms, isAdmin, user?.id],
  );

  return (
    <>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <ResourceGrid
        title="Users"
        rows={rows}
        columns={columns}
        loading={loading}
        emptyLabel="No users yet."
        headerAction={isAdmin ? <AddButton label="Add user" onClick={openCreate} /> : undefined}
      />
      <FormDialog
        open={formOpen}
        title={editing ? "Edit user" : "Add user"}
        error={formError}
        submitting={submitting}
        onClose={() => setFormOpen(false)}
        onSubmit={onSubmit}
      >
        <TextField
          label="Full name"
          value={draft.full_name}
          onChange={(e) => setDraft({ ...draft, full_name: e.target.value })}
          required
          fullWidth
          margin="dense"
        />
        <TextField
          label="Email"
          type="email"
          value={draft.email}
          onChange={(e) => setDraft({ ...draft, email: e.target.value })}
          required
          fullWidth
          margin="dense"
        />
        <TextField
          label={editing ? "New password (optional)" : "Password"}
          type="password"
          value={draft.password}
          onChange={(e) => setDraft({ ...draft, password: e.target.value })}
          required={!editing}
          fullWidth
          margin="dense"
          inputProps={{ minLength: editing ? undefined : 8 }}
        />
        <TextField
          select
          label="Role"
          value={draft.role}
          onChange={(e) => setDraft({ ...draft, role: e.target.value as UserRole })}
          required
          fullWidth
          margin="dense"
        >
          {USER_ROLES.map((role) => (
            <MenuItem key={role} value={role}>
              {ROLE_LABEL[role]}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          label="Home farm"
          value={draft.farm_id}
          onChange={(e) => setDraft({ ...draft, farm_id: e.target.value })}
          fullWidth
          margin="dense"
        >
          <MenuItem value="">None</MenuItem>
          {farms.map((farm) => (
            <MenuItem key={farm.id} value={farm.id}>
              {farm.name}
            </MenuItem>
          ))}
        </TextField>
        <FormControlLabel
          control={
            <Switch checked={draft.is_active} onChange={(e) => setDraft({ ...draft, is_active: e.target.checked })} />
          }
          label="Active"
        />
      </FormDialog>
      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Delete user"
        body={pendingDelete ? `Delete ${pendingDelete.full_name}?` : ""}
        onClose={() => setPendingDelete(null)}
        onConfirm={confirmDelete}
        busy={deleting}
      />
    </>
  );
}
