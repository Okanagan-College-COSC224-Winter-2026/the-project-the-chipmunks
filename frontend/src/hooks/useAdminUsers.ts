import { useState, useEffect, useCallback } from 'react';
import {
  adminListUsers,
  adminDeactivateUser,
  adminReactivateUser,
} from '../util/api';

export interface AdminUser {
  id: number;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
}

export function useAdminUsers() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [role, setRole] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await adminListUsers(page, role, search);
      if (!res || !res.ok) throw new Error('Failed to load');
      const data = await res.json();
      setUsers(data.users || []);
      setTotal(data.total || 0);
    } catch {
      setError('Failed to load users.');
    } finally {
      setLoading(false);
    }
  }, [page, role, search]);

  useEffect(() => {
    load();
  }, [load]);

  const deactivate = async (id: number) => {
    await adminDeactivateUser(id);
    load();
  };

  const reactivate = async (id: number) => {
    await adminReactivateUser(id);
    load();
  };

  return {
    users, total, page, setPage,
    role, setRole,
    search, setSearch,
    loading, error,
    deactivate, reactivate,
    reload: load,
  };
}
