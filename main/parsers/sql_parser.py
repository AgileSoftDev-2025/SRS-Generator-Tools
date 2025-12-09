import re
import sqlparse

def parse_sql_file(sql_content):
    tables = {}
    foreign_keys = []

    # Split statements
    statements = sqlparse.split(sql_content)

    for stmt in statements:
        stmt_clean = stmt.strip()
        if not stmt_clean.lower().startswith("create table"):
            continue

        # --- FIX 1: Regex CREATE TABLE yang fleksibel ---
        match = re.search(
            r'CREATE\s+TABLE\s+[`"]?(\w+)[`"]?\s*\((.*?)\)\s*;',
            stmt_clean,
            re.S | re.I
        )
        if not match:
            continue

        table_name = match.group(1)
        columns_block = match.group(2)

        # --- FIX 2: Split kolom aman (tidak memecah FK) ---
        column_lines = re.split(r',\s*(?![^()]*\))', columns_block)

        columns = []

        for line in column_lines:
            line = line.strip()

            # Skip PK/FK/constraint lines
            if not line or line.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "KEY", "CONSTRAINT")):
                continue

            # Ambil kolom normal
            col_match = re.match(r'[`"]?(\w+)[`"]?\s+(.*)', line, re.I)
            if col_match:
                col_name = col_match.group(1)
                col_type = col_match.group(2)

                columns.append({
                    "name": col_name,
                    "type": col_type
                })

        tables[table_name] = columns

        # --- FIX 3: Regex FOREIGN KEY yang stabil ---
        fk_matches = re.findall(
            r'FOREIGN KEY\s*\((\w+)\)\s*REFERENCES\s+(\w+)\s*\((\w+)\)',
            stmt_clean,
            re.I
        )

        for fk_col, ref_table, ref_col in fk_matches:
            foreign_keys.append({
                "table": table_name,
                "column": fk_col,
                "ref_table": ref_table,
                "ref_column": ref_col,
            })

    return {
        "tables": tables,
        "relationships": foreign_keys,
    }
