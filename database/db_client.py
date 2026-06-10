import streamlit as st
import psycopg2
import psycopg2.extras
from decimal import Decimal
from typing import Any, Dict, List, Optional


def _convert_decimals(data: List[Dict]) -> List[Dict]:
    result = []
    for row in data:
        new_row = {}
        for k, v in row.items():
            new_row[k] = float(v) if isinstance(v, Decimal) else v
        result.append(new_row)
    return result


class Response:
    def __init__(self, data: List[Dict]):
        self.data = _convert_decimals(data) if data else []


class QueryBuilder:
    def __init__(self, conn, table_name: str):
        self._conn = conn
        self._table_name = table_name
        self._filters_eq: List[tuple] = []
        self._filters_neq: List[tuple] = []
        self._select_cols = "*"
        self._is_delete = False
        self._is_update = False
        self._update_data: Optional[Dict] = None
        self._insert_data: Any = None
        self._limit_val: Optional[int] = None

    def select(self, cols: str = "*"):
        self._select_cols = cols
        return self

    def eq(self, column: str, value: Any):
        self._filters_eq.append((column, value))
        return self

    def neq(self, column: str, value: Any):
        self._filters_neq.append((column, value))
        return self

    def insert(self, data: Any):
        self._insert_data = data
        return self

    def update(self, data: Dict):
        self._update_data = data
        self._is_update = True
        return self

    def delete(self):
        self._is_delete = True
        return self

    def limit(self, n: int = 1):
        self._limit_val = n
        return self

    def execute(self) -> Response:
        try:
            with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if self._is_delete:
                    sql, params = self._build_sql("DELETE")
                    cur.execute(sql, params)
                    result = [dict(r) for r in cur.fetchall()]
                    self._conn.commit()
                    return Response(result)

                elif self._is_update and self._update_data:
                    set_clauses, set_params = self._build_set()
                    where_clauses, where_params = self._build_where()
                    sql = f'UPDATE "{self._table_name}" SET {set_clauses} {where_clauses} RETURNING *'
                    cur.execute(sql, set_params + where_params)
                    result = [dict(r) for r in cur.fetchall()]
                    self._conn.commit()
                    return Response(result)

                elif self._insert_data is not None:
                    return self._do_insert(cur)

                else:
                    where_clauses, params = self._build_where()
                    sql = f'SELECT {self._select_cols} FROM "{self._table_name}" {where_clauses}'
                    if self._limit_val is not None:
                        sql += f" LIMIT {self._limit_val}"
                    cur.execute(sql, params)
                    result = [dict(r) for r in cur.fetchall()]
                    return Response(result)

        except Exception as e:
            try:
                self._conn.rollback()
            except Exception:
                pass
            raise e

    def _do_insert(self, cur):
        if isinstance(self._insert_data, list):
            if not self._insert_data:
                return Response([])
            cols = list(self._insert_data[0].keys())
            col_names = ", ".join(f'"{c}"' for c in cols)
            values = []
            for item in self._insert_data:
                values.append(tuple(item.get(c) for c in cols))
            sql = f'INSERT INTO "{self._table_name}" ({col_names}) VALUES %s RETURNING *'
            psycopg2.extras.execute_values(cur, sql, values, template=None)
            result = [dict(r) for r in cur.fetchall()]
            self._conn.commit()
            return Response(result)
        else:
            cols = list(self._insert_data.keys())
            vals = [self._insert_data[c] for c in cols]
            col_names = ", ".join(f'"{c}"' for c in cols)
            placeholders = ", ".join(["%s"] * len(cols))
            sql = f'INSERT INTO "{self._table_name}" ({col_names}) VALUES ({placeholders}) RETURNING *'
            cur.execute(sql, vals)
            result = [dict(r) for r in cur.fetchall()]
            self._conn.commit()
            return Response(result)

    def _build_where(self):
        clauses = []
        params = []
        for col, val in self._filters_eq:
            clauses.append(f'"{col}" = %s')
            params.append(val)
        for col, val in self._filters_neq:
            clauses.append(f'"{col}" != %s')
            params.append(val)
        if clauses:
            return "WHERE " + " AND ".join(clauses), params
        return "", []

    def _build_set(self):
        clauses = []
        params = []
        for col, val in self._update_data.items():
            clauses.append(f'"{col}" = %s')
            params.append(val)
        return ", ".join(clauses), params


@st.cache_resource(show_spinner=False)
def _get_connection(database_url: str):
    return psycopg2.connect(database_url, keepalives=1, keepalives_idle=30)


class PgClient:
    def __init__(self, connection_string: Optional[str] = None):
        if connection_string is None:
            try:
                connection_string = st.secrets["database"]["DATABASE_URL"]
            except Exception:
                import os
                connection_string = os.environ.get("DATABASE_URL", "")
                if not connection_string:
                    raise RuntimeError(
                        "DATABASE_URL no encontrada. En Render: Settings -> Environment -> agregar DATABASE_URL. "
                        "En local: .streamlit/secrets.toml con [database] DATABASE_URL = \"...\""
                    )
        self._connection_string = connection_string

    def table(self, name: str) -> QueryBuilder:
        conn = _get_connection(self._connection_string)
        return QueryBuilder(conn, name)

    def rpc(self, *args, **kwargs):
        return Response([])
