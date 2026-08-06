// Generates Supabase-style TypeScript types by introspecting the LIVE database.
// Used because `supabase gen types` requires Docker, which is unavailable here.
// Output shape matches `supabase gen types typescript` closely enough to be a
// drop-in for typing the supabase-js client.
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';

// psql must be >= the server version (17.x). Override with PSQL_PATH if needed.
const PSQL = process.env.PSQL_PATH || 'psql';

// SUPABASE_DB_URL is a server-side-only secret. It must never be given an
// EXPO_PUBLIC_ prefix and must never be committed.
const dbUrl = process.env.SUPABASE_DB_URL?.trim();
if (!dbUrl) {
  console.error('SUPABASE_DB_URL is not set. Export it before running this script.');
  process.exit(1);
}

const outPath = process.argv[2] || 'src/types/database.types.ts';

const SEP = '\u0001';

function q(sql) {
  const out = execFileSync(PSQL, [dbUrl, '-At', '-F', SEP, '-c', sql], {
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
  });
  return out
    .split(/\r?\n/)
    .filter((l) => l.length > 0)
    .map((l) => l.split(SEP));
}

// ── Type mapping ────────────────────────────────────────────
function tsType(formatType) {
  const base = formatType.replace(/\[\]$/, '').replace(/\(.*\)$/, '').trim();
  const isArray = formatType.endsWith('[]');
  let t;
  switch (base) {
    case 'uuid': case 'text': case 'character varying': case 'character':
    case 'name': case 'citext': case 'bpchar':
    case 'timestamp with time zone': case 'timestamp without time zone':
    case 'date': case 'time without time zone': case 'time with time zone':
    case 'interval': case 'inet': case 'bytea':
      t = 'string'; break;
    case 'smallint': case 'integer': case 'bigint': case 'numeric':
    case 'real': case 'double precision': case 'oid':
      t = 'number'; break;
    case 'boolean':
      t = 'boolean'; break;
    case 'json': case 'jsonb':
      t = 'Json'; break;
    case 'void':
      t = 'undefined'; break;
    default:
      // PostGIS geography/geometry and anything else we do not model.
      t = 'unknown';
  }
  return isArray ? `${t}[]` : t;
}

// ── Tables (excluding extension-owned, e.g. postgis spatial_ref_sys) ──
const tables = q(`
  SELECT c.relname
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname = 'public'
    AND c.relkind IN ('r','p','u')
    AND NOT EXISTS (
      SELECT 1 FROM pg_depend d
      WHERE d.objid = c.oid AND d.deptype = 'e'
    )
  ORDER BY c.relname
`).map((r) => r[0]);

const columns = q(`
  SELECT c.relname,
         a.attname,
         format_type(a.atttypid, a.atttypmod),
         CASE WHEN a.attnotnull THEN 'f' ELSE 't' END AS nullable,
         CASE WHEN ad.adbin IS NOT NULL THEN 't' ELSE 'f' END AS has_default,
         CASE WHEN a.attgenerated <> '' THEN 't' ELSE 'f' END AS generated
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
  LEFT JOIN pg_attrdef ad ON ad.adrelid = c.oid AND ad.adnum = a.attnum
  WHERE n.nspname = 'public'
    AND c.relkind IN ('r','p','u')
    AND NOT EXISTS (
      SELECT 1 FROM pg_depend d WHERE d.objid = c.oid AND d.deptype = 'e'
    )
  ORDER BY c.relname, a.attnum
`);

// ── Functions (excluding extension-owned: postgis et al.) ──
const funcs = q(`
  SELECT p.proname,
         pg_get_function_arguments(p.oid),
         pg_get_function_result(p.oid),
         p.proretset::text
  FROM pg_proc p
  JOIN pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname = 'public'
    AND p.prokind = 'f'
    AND NOT EXISTS (
      SELECT 1 FROM pg_depend d WHERE d.objid = p.oid AND d.deptype = 'e'
    )
  ORDER BY p.proname
`);

// ── Emit ────────────────────────────────────────────────────
const byTable = new Map();
for (const [table, name, type, nullable, hasDefault, generated] of columns) {
  if (!byTable.has(table)) byTable.set(table, []);
  byTable.get(table).push({
    name,
    type,
    nullable: nullable === 't',
    hasDefault: hasDefault === 't',
    generated: generated === 't',
  });
}

let out = `// ============================================================
// Project "Relief" — Generated Supabase Database Types
// ============================================================
// GENERATED FILE — do not edit by hand.
//
// Source: the LIVE Supabase project, introspected from
// pg_catalog on 2026-08-06 (PostgreSQL 17.6).
//
// Regenerate with:
//   npm run gen:types      (requires SUPABASE_DB_URL)
//
// Note: \`supabase gen types typescript\` requires Docker. Where
// Docker is unavailable, tools/generate-database-types.mjs
// performs the same introspection over a direct connection and
// emits this file. Extension-owned objects (PostGIS) are
// excluded; geography/geometry columns are typed \`unknown\`
// because they are not consumed by the client.
// ============================================================

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  public: {
    Tables: {
`;

for (const table of tables) {
  const cols = byTable.get(table) || [];
  out += `      ${table}: {\n        Row: {\n`;
  for (const c of cols) {
    out += `          ${c.name}: ${tsType(c.type)}${c.nullable ? ' | null' : ''};\n`;
  }
  out += `        };\n        Insert: {\n`;
  for (const c of cols) {
    if (c.generated) continue; // generated columns cannot be written
    const optional = c.nullable || c.hasDefault;
    out += `          ${c.name}${optional ? '?' : ''}: ${tsType(c.type)}${c.nullable ? ' | null' : ''};\n`;
  }
  out += `        };\n        Update: {\n`;
  for (const c of cols) {
    if (c.generated) continue;
    out += `          ${c.name}?: ${tsType(c.type)}${c.nullable ? ' | null' : ''};\n`;
  }
  out += `        };\n        Relationships: [];\n      };\n`;
}

out += `    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
`;

function parseArgs(argString) {
  if (!argString.trim()) return [];
  // Split on top-level commas only.
  const parts = [];
  let depth = 0;
  let cur = '';
  for (const ch of argString) {
    if (ch === '(') depth++;
    if (ch === ')') depth--;
    if (ch === ',' && depth === 0) { parts.push(cur); cur = ''; continue; }
    cur += ch;
  }
  if (cur.trim()) parts.push(cur);

  return parts.map((raw) => {
    let s = raw.trim();
    let hasDefault = false;
    const defIdx = s.search(/\sDEFAULT\s/i);
    if (defIdx !== -1) { hasDefault = true; s = s.slice(0, defIdx).trim(); }
    s = s.replace(/^(IN|OUT|INOUT|VARIADIC)\s+/i, '');
    const space = s.indexOf(' ');
    if (space === -1) return null; // unnamed arg — cannot map to a JS key
    return { name: s.slice(0, space), type: s.slice(space + 1).trim(), hasDefault };
  }).filter(Boolean);
}

function parseReturns(result, retset) {
  const isSet = retset === 't' || /^SETOF /i.test(result);
  const tableMatch = result.match(/^TABLE\((.*)\)$/is);
  if (tableMatch) {
    const cols = parseArgs(tableMatch[1]);
    const body = cols.map((c) => `            ${c.name}: ${tsType(c.type)} | null;`).join('\n');
    return `{\n${body}\n        }[]`;
  }
  const scalar = result.replace(/^SETOF /i, '').trim();
  const t = tsType(scalar);
  return isSet ? `${t}[]` : t;
}

for (const [name, args, result, retset] of funcs) {
  const parsed = parseArgs(args);
  out += `      ${name}: {\n        Args: {`;
  if (parsed.length === 0) {
    out += ` [_ in never]: never };\n`;
  } else {
    out += `\n`;
    for (const a of parsed) {
      out += `          ${a.name}${a.hasDefault ? '?' : ''}: ${tsType(a.type)};\n`;
    }
    out += `        };\n`;
  }
  out += `        Returns: ${parseReturns(result, retset)};\n      };\n`;
}

out += `    };
    Enums: {
      [_ in never]: never;
    };
    CompositeTypes: {
      [_ in never]: never;
    };
  };
};

// ── Convenience aliases ─────────────────────────────────────
export type Tables<T extends keyof Database['public']['Tables']> =
  Database['public']['Tables'][T]['Row'];
export type TablesInsert<T extends keyof Database['public']['Tables']> =
  Database['public']['Tables'][T]['Insert'];
export type TablesUpdate<T extends keyof Database['public']['Tables']> =
  Database['public']['Tables'][T]['Update'];
export type Functions<T extends keyof Database['public']['Functions']> =
  Database['public']['Functions'][T];
`;

fs.writeFileSync(outPath, out);
console.log('wrote', outPath);
console.log('tables:', tables.length, 'functions:', funcs.length);
