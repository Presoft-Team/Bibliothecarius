import { useEffect, useState } from "react";
import { ShieldCheck, ShieldOff } from "lucide-react";
import { adminUsersApi } from "../lib/resources";
import { useAuth } from "../lib/AuthContext";
import { keycloak } from "../lib/keycloak";
import { getErrorMessage } from "../lib/errors";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import Field, { inputClass } from "../components/ui/Field";
import type { AdminUser, AdminUserInviteResult } from "../lib/types";

export default function UsersPage() {
  const { currentUser, loading: authLoading } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [tempPassword, setTempPassword] = useState("");
  const [invited, setInvited] = useState<AdminUserInviteResult | null>(null);

  const load = () => {
    setLoading(true);
    adminUsersApi
      .list()
      .then(setUsers)
      .catch(() => setError("Failed to load users"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (currentUser?.role === "admin") load();
  }, [currentUser]);

  if (authLoading) return <p className="text-sm text-slate-400">Loading…</p>;
  if (currentUser?.role !== "admin") {
    return <p className="text-sm text-red-600 dark:text-red-400">You need admin access to view this page.</p>;
  }

  const invite = async () => {
    setError(null);
    try {
      const result = await adminUsersApi.invite(username, email, tempPassword);
      setInvited(result);
      setUsername("");
      setEmail("");
      setTempPassword("");
      load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to invite user — username or email may already be taken"));
    }
  };

  const toggleAdmin = async (user: AdminUser) => {
    const isAdmin = user.roles.includes("admin");
    try {
      if (isAdmin) {
        await adminUsersApi.revokeRole(user.keycloak_id, "admin");
      } else {
        await adminUsersApi.grantRole(user.keycloak_id, "admin");
      }
      load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to change role (you cannot revoke your own admin role)"));
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Users</h1>

      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

      {loading ? (
        <p className="text-sm text-slate-400">Loading…</p>
      ) : (
        <div className="space-y-2">
          {users.map((u) => {
            const isAdmin = u.roles.includes("admin");
            const isSelf = u.username === keycloak.tokenParsed?.preferred_username;
            return (
              <Card key={u.keycloak_id} className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex min-w-0 items-center gap-2">
                    <strong className="shrink-0 text-slate-800 dark:text-slate-100">{u.username}</strong>
                    <span className="min-w-0 truncate text-sm text-slate-400">{u.email}</span>
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {u.roles.map((r) => (
                      <Badge key={r}>{r}</Badge>
                    ))}
                    {!u.provisioned && <Badge variant="warn">never logged in</Badge>}
                  </div>
                </div>
                <Button
                  size="sm"
                  variant={isAdmin ? "danger" : "secondary"}
                  disabled={isSelf && isAdmin}
                  onClick={() => toggleAdmin(u)}
                >
                  {isAdmin ? <ShieldOff className="h-3.5 w-3.5" /> : <ShieldCheck className="h-3.5 w-3.5" />}
                  {isAdmin ? "Revoke admin" : "Grant admin"}
                </Button>
              </Card>
            );
          })}
        </div>
      )}

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-500 dark:text-slate-400">Invite a user</h2>
        <Field label="Username">
          <input
            name="invite-username"
            className={inputClass}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </Field>
        <Field label="Email">
          <input
            name="invite-email"
            type="email"
            className={inputClass}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>
        <Field label="Temporary password">
          <input
            name="invite-temp-password"
            autoComplete="new-password"
            className={inputClass}
            type="password"
            value={tempPassword}
            onChange={(e) => setTempPassword(e.target.value)}
          />
        </Field>
        <Button variant="primary" disabled={!username || !email || !tempPassword} onClick={invite}>
          Invite
        </Button>

        {invited && (
          <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
            Created <strong className="text-slate-700 dark:text-slate-200">{invited.username}</strong>. Share
            this temporary password out of band — it won't be shown again:{" "}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
              {invited.temporary_password}
            </code>
          </p>
        )}
      </Card>
    </div>
  );
}
