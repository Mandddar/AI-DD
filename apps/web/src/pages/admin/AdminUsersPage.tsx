import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Users, Shield, Loader2, UserCheck, UserX, ChevronDown } from 'lucide-react';
import { api } from '../../api/client';
import type { User } from '../../types';

const ROLE_LABELS: Record<string, string> = {
  admin: 'Admin',
  lead_advisor: 'Lead Advisor',
  team_advisor: 'Team Advisor',
  seller: 'Seller',
  buyer: 'Buyer / Investor',
};

const ROLE_OPTIONS = ['admin', 'lead_advisor', 'team_advisor', 'seller', 'buyer'];

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-gold/10 text-gold ring-gold/20',
  lead_advisor: 'bg-blue-500/10 text-blue-400 ring-blue-500/20',
  team_advisor: 'bg-purple-500/10 text-purple-400 ring-purple-500/20',
  seller: 'bg-green-500/10 text-green-400 ring-green-500/20',
  buyer: 'bg-text-muted/10 text-text-secondary ring-text-muted/20',
};

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [editingUser, setEditingUser] = useState<string | null>(null);

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => api.get<User[]>('/auth/users').then(r => r.data),
  });

  const updateRole = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      api.patch(`/auth/users/${userId}/role`, { role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setEditingUser(null);
    },
  });

  const toggleActive = useMutation({
    mutationFn: ({ userId, is_active }: { userId: string; is_active: boolean }) =>
      api.patch(`/auth/users/${userId}/active`, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-gold" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Users className="w-8 h-8 text-gold" />
          <div>
            <h1 className="text-3xl font-display font-bold text-text-primary">Team Management</h1>
            <p className="text-base text-text-secondary mt-0.5">{users.length} registered user{users.length !== 1 ? 's' : ''}</p>
          </div>
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-base">
          <thead>
            <tr className="border-b border-canvas-border bg-surface/30">
              <th className="p-4 text-left text-text-secondary font-medium">User</th>
              <th className="p-4 text-left text-text-secondary font-medium">Role</th>
              <th className="p-4 text-left text-text-secondary font-medium">Status</th>
              <th className="p-4 text-left text-text-secondary font-medium">Joined</th>
              <th className="p-4 text-right text-text-secondary font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id} className="border-b border-canvas-border/50 hover:bg-surface/20 transition-colors">
                <td className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface text-sm font-medium text-text-secondary">
                      {user.full_name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-text-primary font-medium">{user.full_name}</p>
                      <p className="text-text-muted text-sm">{user.email}</p>
                    </div>
                  </div>
                </td>
                <td className="p-4">
                  {editingUser === user.id ? (
                    <select
                      className="input text-sm py-1 px-2"
                      defaultValue={user.role}
                      onChange={e => {
                        updateRole.mutate({ userId: user.id, role: e.target.value });
                      }}
                      onBlur={() => setEditingUser(null)}
                      autoFocus
                    >
                      {ROLE_OPTIONS.map(r => (
                        <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                      ))}
                    </select>
                  ) : (
                    <button
                      onClick={() => setEditingUser(user.id)}
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-sm font-medium ring-1 ${ROLE_COLORS[user.role] || ''} hover:opacity-80 transition-opacity`}
                    >
                      {ROLE_LABELS[user.role] || user.role}
                      <ChevronDown size={12} />
                    </button>
                  )}
                </td>
                <td className="p-4">
                  <span className={`inline-flex items-center gap-1 text-sm font-medium ${
                    user.is_active ? 'text-risk-low' : 'text-risk-high'
                  }`}>
                    {user.is_active ? <UserCheck size={14} /> : <UserX size={14} />}
                    {user.is_active ? 'Active' : 'Disabled'}
                  </span>
                </td>
                <td className="p-4 text-text-muted text-sm">
                  {new Date(user.created_at).toLocaleDateString()}
                </td>
                <td className="p-4 text-right">
                  <button
                    className={`btn-ghost text-sm px-2.5 py-1.5 ${
                      user.is_active ? 'text-risk-high hover:bg-risk-high/10' : 'text-risk-low hover:bg-risk-low/10'
                    }`}
                    onClick={() => toggleActive.mutate({ userId: user.id, is_active: !user.is_active })}
                    disabled={toggleActive.isPending}
                  >
                    {user.is_active ? 'Disable' : 'Enable'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-sm text-text-muted italic">
        Click a role badge to change a user's role. Use the Add Member feature on deal pages to assign users to specific deals.
      </p>
    </div>
  );
}
