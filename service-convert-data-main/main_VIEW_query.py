import logging
from psycopg2 import sql
from connectDB import (
    get_main_db_connection,
    get_vector_db_connection,
)

from logServer import setup_logging
from data_material import batch_classify_materials

def validate_main_tables_exist():
    conn = get_main_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
            AND table_name IN ('ListMaterialsBOQ', 'MD_Material_SAP');
    """)

    tables = {row[0] for row in cur.fetchall()}
    cur.close()
    conn.close()

    missing = {"ListMaterialsBOQ", "MD_Material_SAP"} - tables
    if missing:
        raise RuntimeError(f"Missing tables in MAIN DB: {missing}")


def generate_cross_db_view_sql(
    fdw_schema,
    table_1,
    table_2,
    columns_t1,
    columns_t2,
    alias_columns,
    join_condition,
    view_schema,
    view_name,
    separator=" - ",
):
    """(Giữ lại để tham khảo SQL VIEW, nhưng không còn dùng để CREATE VIEW).

    Hàm này hiện không còn được dùng trong main(); logic chính đã
    chuyển sang tạo bảng merge trong VECTOR DB để tránh lỗi quyền
    CREATE VIEW trên MAIN DB.
    """

    select_parts = []
    for c1, c2, alias in zip(columns_t1, columns_t2, alias_columns):
        select_parts.append(
            f"CONCAT_WS('{separator}', "
            f"t1.\"{c1}\", t2.\"{c2}\") AS \"{alias}\""
        )

    return f"""
            CREATE OR REPLACE VIEW "{view_schema}".{view_name} AS
            SELECT
                {", ".join(select_parts)}
            FROM "{fdw_schema}"."{table_1}" t1
            JOIN "{fdw_schema}"."{table_2}" t2
                ON {join_condition};
            """.strip()


def build_merge_rows_from_main_db():
    """Đọc dữ liệu join từ MAIN DB, trả về list row merge.

    Kết quả mỗi row: (idMaterial, ID_Material_SAP, name, description)
    """

    conn = get_main_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT
                    t1."idMaterial"          AS id_material,
                    t2."ID_Material_SAP"     AS id_material_sap,
                    CONCAT_WS(' - ',
                                t1."NameMaterial",
                                t2."Des_Material_Sap") AS name,
                    CONCAT_WS(' - ',
                                t1."idMaterial",
                                t2."ID_Material_SAP")  AS description
                FROM public."ListMaterialsBOQ" t1
                JOIN public."MD_Material_SAP" t2
                    ON t1."idMaterial" = t2."ID_Material_SAP";
                '''
            )
            rows = cur.fetchall()
            logging.info(f"Đã đọc {len(rows)} dòng merge từ MAIN DB")
            return rows
    finally:
        conn.close()


def sync_merge_to_vector_db(rows):
    """Ghi dữ liệu merge vào VECTOR DB dưới dạng bảng vật lý.
    Tạo bảng nếu chưa có, sau đó xóa dữ liệu cũ và insert lại.
    """

    if not rows:
        logging.info("Không có dữ liệu merge để sync sang VECTOR DB")
        return

    conn = get_vector_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS public.merge_material (
                    id_material       TEXT,
                    id_material_sap   TEXT,
                    name              TEXT,
                    description       TEXT
                );
                '''
            )

            cur.execute('TRUNCATE TABLE public.merge_material;')

            insert_sql = '''
                INSERT INTO public.merge_material
                    (id_material, id_material_sap, name, description)
                VALUES (%s, %s, %s, %s);
            '''

            cur.executemany(insert_sql, rows)
            conn.commit()

        logging.info(f"Đã sync {len(rows)} dòng vào VECTOR DB (bảng public.merge_material)")
    finally:
        conn.close()


def main():
    try:
        logging.info("Validate source tables in MAIN DB")
        validate_main_tables_exist()

        logging.info("Đọc dữ liệu merge từ MAIN DB")
        rows = build_merge_rows_from_main_db()

        logging.info("Ghi dữ liệu merge vào VECTOR DB")
        sync_merge_to_vector_db(rows)

        logging.info("Hoàn tất sync bảng merge_material trong VECTOR DB")

    except Exception:
        logging.exception("Create VIEW failed")
        raise


# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    log_file = setup_logging(log_dir="logs", name="convertDB")
    main()