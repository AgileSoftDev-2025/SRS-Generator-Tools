from main.models import ImportedColumn, ImportedRelationship, ImportedTable

def save_parsed_sql_to_db(parsed_result):
    tables_data = parsed_result.get("tables", {})
    relationships_data = parsed_result.get("relationships", [])

    # Hapus data lama kalau kamu ingin hasil import baru menggantikan yang lama
    ImportedRelationship.objects.all().delete()
    ImportedColumn.objects.all().delete()
    ImportedTable.objects.all().delete()

    # Simpan tabel dan kolom
    table_objs = {}
    for table_name, columns in tables_data.items():
        table_obj = ImportedTable.objects.create(name=table_name)
        table_objs[table_name] = table_obj

        for col in columns:
            ImportedColumn.objects.create(
                table=table_obj,
                name=col["name"],
                data_type=col["type"]
            )

    # Simpan relationships
    for rel in relationships_data:
        table_obj = table_objs.get(rel["table"])
        ref_table_obj = table_objs.get(rel["ref_table"])

        if table_obj and ref_table_obj:
            ImportedRelationship.objects.create(
                table=table_obj,
                column_name=rel["column"],
                ref_table=ref_table_obj,
                ref_column_name=rel["ref_column"]
            )
