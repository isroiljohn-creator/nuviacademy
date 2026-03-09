import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { Pool } from "https://deno.land/x/postgres@v0.17.0/mod.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Create a connection pool
const pool = new Pool(Deno.env.get("RAILWAY_DATABASE_URL")!, 3, true);

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { action, table, data, filters } = await req.json();
    console.log(`DB action: ${action} on table: ${table}`);

    const connection = await pool.connect();
    let result;

    try {
      switch (action) {
        case 'select': {
          let query = `SELECT * FROM ${table}`;
          const values: any[] = [];
          
          if (filters && Object.keys(filters).length > 0) {
            const conditions = Object.entries(filters).map(([key, _], index) => {
              values.push(filters[key]);
              return `${key} = $${index + 1}`;
            });
            query += ` WHERE ${conditions.join(' AND ')}`;
          }
          
          console.log(`Query: ${query}`, values);
          result = await connection.queryObject(query, values);
          break;
        }
        
        case 'insert': {
          const keys = Object.keys(data);
          const values = Object.values(data);
          const placeholders = keys.map((_, i) => `$${i + 1}`).join(', ');
          const query = `INSERT INTO ${table} (${keys.join(', ')}) VALUES (${placeholders}) RETURNING *`;
          
          console.log(`Query: ${query}`, values);
          result = await connection.queryObject(query, values);
          break;
        }
        
        case 'update': {
          const { id, ...updateData } = data;
          const keys = Object.keys(updateData);
          const values = Object.values(updateData);
          const setClause = keys.map((key, i) => `${key} = $${i + 1}`).join(', ');
          values.push(id);
          const query = `UPDATE ${table} SET ${setClause} WHERE id = $${values.length} RETURNING *`;
          
          console.log(`Query: ${query}`, values);
          result = await connection.queryObject(query, values);
          break;
        }
        
        case 'upsert': {
          const keys = Object.keys(data);
          const values = Object.values(data);
          const placeholders = keys.map((_, i) => `$${i + 1}`).join(', ');
          const updateClause = keys.map((key, i) => `${key} = $${i + 1}`).join(', ');
          
          // Using ON CONFLICT for upsert
          const conflictKey = filters?.conflict_key || 'id';
          const query = `
            INSERT INTO ${table} (${keys.join(', ')}) 
            VALUES (${placeholders}) 
            ON CONFLICT (${conflictKey}) 
            DO UPDATE SET ${updateClause}
            RETURNING *
          `;
          
          console.log(`Query: ${query}`, values);
          result = await connection.queryObject(query, values);
          break;
        }
        
        case 'delete': {
          const values = [filters.id];
          const query = `DELETE FROM ${table} WHERE id = $1 RETURNING *`;
          
          console.log(`Query: ${query}`, values);
          result = await connection.queryObject(query, values);
          break;
        }
        
        default:
          throw new Error(`Unknown action: ${action}`);
      }
      
      return new Response(JSON.stringify({ data: result.rows, error: null }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
      
    } finally {
      connection.release();
    }
    
  } catch (error: unknown) {
    console.error('Database error:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return new Response(JSON.stringify({ data: null, error: errorMessage }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
