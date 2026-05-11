/**
 * PULSE frontend shared types.
 *
 * B-01/B-02 fix: Role TS union uses the SIX spec names verbatim from
 * REQ-user-roles / CONTEXT.md §Auth. These map 1-1 to the rows seeded in
 * Plan 05's 0002_auth_users_roles migration (`super_admin`, `admin_unit`,
 * `pic_bidang`, `asesor`, `manajer_unit`, `viewer`).
 *
 * ProtectedRoute `allow=[...]` arrays, role-based nav visibility, and any
 * other surface that compares against `user.roles` must use these strings
 * verbatim. No capitalized "Admin" / "PIC" / "Asesor" anywhere.
 */
export type Role =
  | "super_admin"
  | "admin_unit"
  | "pic_bidang"
  | "asesor"
  | "manajer_unit"
  | "viewer";

/**
 * Backend `UserPublic` DTO shape — mirrors `backend/app/schemas/user.py`.
 * The `roles` field is a list of role names (already flattened server-side
 * by the `_flatten_roles` model_validator), and `bidang_id` is nullable
 * because admin_unit / super_admin do not need to be pinned to a single
 * bidang.
 */
export interface UserPublic {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  bidang_id: string | null;
  roles: Role[];
}
