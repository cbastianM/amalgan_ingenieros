# database/demo_client.py
# Mock Supabase client that stores all data in st.session_state
# This allows the app to run as a DEMO without any database connection.
import streamlit as st
import copy
import uuid
from typing import Any, Dict, List, Optional


class DemoResponse:
    def __init__(self, data: List[Dict]):
        self.data = data if data else []


class DemoQueryBuilder:
    def __init__(self, store: dict, table_name: str, store_key: str):
        self._store = store
        self._table_name = table_name
        self._store_key = store_key
        self._filters_eq: List[tuple] = []
        self._filters_neq: List[tuple] = []
        self._select_cols = "*"
        self._is_delete = False
        self._is_update = False
        self._update_data: Optional[Dict] = None
        self._insert_data: Any = None

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
        self._limit = n
        return self

    def execute(self) -> DemoResponse:
        rows = self._store.get(self._store_key, [])

        # ═══ DELETE ═══
        if self._is_delete:
            to_remove = self._apply_filters(rows)
            if to_remove:
                id_col = self._detect_id_col(rows)
                remove_ids = {r.get(id_col) for r in to_remove}
                self._store[self._store_key] = [
                    r for r in self._store.get(self._store_key, [])
                    if r.get(id_col) not in remove_ids
                ]
            return DemoResponse(to_remove)

        # ═══ UPDATE ═══
        if self._is_update and self._update_data is not None:
            updated_rows = []
            for row in self._store.get(self._store_key, []):
                if self._row_matches(row):
                    row.update(self._update_data)
                    updated_rows.append(copy.deepcopy(row))
            return DemoResponse(updated_rows)

        # ═══ INSERT ═══
        if self._insert_data is not None:
            if isinstance(self._insert_data, list):
                inserted = []
                for item in self._insert_data:
                    row = copy.deepcopy(item)
                    if "id" not in row:
                        row["id"] = str(uuid.uuid4())[:8]
                    self._store.setdefault(self._store_key, []).append(row)
                    inserted.append(copy.deepcopy(row))
                return DemoResponse(inserted)
            else:
                row = copy.deepcopy(self._insert_data)
                if "id" not in row:
                    row["id"] = str(uuid.uuid4())[:8]
                self._store.setdefault(self._store_key, []).append(row)
                return DemoResponse([copy.deepcopy(row)])

        # ═══ SELECT ═══
        filtered = self._apply_filters(rows)
        if hasattr(self, "_limit") and self._limit:
            filtered = filtered[:self._limit]
        return DemoResponse(filtered)

    def _detect_id_col(self, rows: List[Dict]) -> str:
        if not rows:
            return "id"
        first = rows[0]
        for candidate in ["id", "id_tarea", "nit"]:
            if candidate in first:
                return candidate
        return "id"

    def _row_matches(self, row: Dict) -> bool:
        for col, val in self._filters_eq:
            row_val = row.get(col)
            if isinstance(row_val, bool) and isinstance(val, bool):
                if row_val != val:
                    return False
            elif str(row_val) != str(val):
                return False
        for col, val in self._filters_neq:
            if str(row.get(col, "")) == str(val):
                return False
        return True

    def _apply_filters(self, rows: List[Dict]) -> List[Dict]:
        return [copy.deepcopy(r) for r in rows if self._row_matches(r)]


class DemoClient:
    def __init__(self):
        if "_demo_db" not in st.session_state:
            st.session_state._demo_db = {}
        self._store = st.session_state._demo_db

    def table(self, name: str) -> DemoQueryBuilder:
        from database.demo_data import init_demo_data
        key = f"tbl_{name}"
        if key not in self._store:
            init_demo_data(self._store, key, name)
        return DemoQueryBuilder(self._store, name, key)

    def rpc(self, *args, **kwargs):
        return DemoResponse([])