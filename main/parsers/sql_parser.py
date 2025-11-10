import re
import sqlparse

def parse_sql_file(sql_content):
    tables = {}
    foreign_keys = []

    # Split SQL statements
    statements = sqlparse.split(sql_content)

    for stmt in statements:
        stmt_clean = stmt.strip()
        if not stmt_clean.lower().startswith("create table"):
            continue

        # Match CREATE TABLE nama_tabel ( ... ) [opsi apapun]
        match = re.search(
            r'CREATE\s+TABLE\s+[`"]?(\w+)[`"]?\s*\((.*?)\)\s*(ENGINE|;|$)',
            stmt_clean,
            re.S | re.I
        )
        if not match:
            continue

        table_name = match.group(1)
        columns_block = match.group(2)
        columns = []

        # Split tiap baris kolom
        for line in columns_block.split(","):
            line = line.strip()
            
            # Baris filter Anda sudah benar, ia akan melewati FOREIGN KEY, PRIMARY KEY, dll.
            if not line or line.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "KEY", "CONSTRAINT")):
                continue

            # Ambil SEMUA sisa baris
            col_match = re.match(r'[`"]?(\w+)[`"]?\s+(.*)', line, re.I)
            
            if col_match:
                columns.append({
                    "name": col_match.group(1),
                    "type": col_match.group(2) 
                })

        tables[table_name] = columns

        # Cari foreign keys 
        fk_matches = re.findall(
            r'FOREIGN KEY\s*\([`"]?(\w+)[`"]?\)\s*REFERENCES\s+[`"]?(\w+)[`"]?\s*\([`"]?(\w+)[`"]?\)',
            stmt_clean,
            re.I
        )
        for fk in fk_matches:
            foreign_keys.append({
                "table": table_name,
                "column": fk[0],
                "ref_table": fk[1],
                "ref_column": fk[2],
            })

    return {
        "tables": tables,
        "relationships": foreign_keys,
    }
