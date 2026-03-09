const DB_URL = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/db`;

interface DbResponse<T> {
  data: T | null;
  error: string | null;
}

async function dbRequest<T>(
  action: string,
  table: string,
  data?: Record<string, unknown>,
  filters?: Record<string, unknown>
): Promise<DbResponse<T>> {
  try {
    const response = await fetch(DB_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY}`,
      },
      body: JSON.stringify({ action, table, data, filters }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('DB request error:', error);
    return { data: null, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}

export const db = {
  select: <T>(table: string, filters?: Record<string, unknown>) =>
    dbRequest<T[]>('select', table, undefined, filters),

  insert: <T>(table: string, data: Record<string, unknown>) =>
    dbRequest<T[]>('insert', table, data),

  update: <T>(table: string, data: Record<string, unknown>) =>
    dbRequest<T[]>('update', table, data),

  upsert: <T>(table: string, data: Record<string, unknown>, conflictKey?: string) =>
    dbRequest<T[]>('upsert', table, data, conflictKey ? { conflict_key: conflictKey } : undefined),

  delete: <T>(table: string, id: string | number) =>
    dbRequest<T[]>('delete', table, undefined, { id }),
};

// Types for your Railway database tables
export interface Profile {
  id: string;
  user_id: string;
  name: string;
  email: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export interface DailyLog {
  id: string;
  user_id: string;
  date: string;
  water_ml: number;
  calories: number;
  protein: number;
  workout_done: boolean;
  created_at: string;
}

export interface Streak {
  id: string;
  user_id: string;
  type: string;
  current_count: number;
  longest_count: number;
  last_date: string;
}
