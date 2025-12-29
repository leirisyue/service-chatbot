from fastapi import APIRouter
from psycopg2.extras import RealDictCursor
import psycopg2
import time
import os
import torch
from transformers import AutoTokenizer, AutoModelForMaskedLM
from config import settings

# =========================================================
# DB
# =========================================================

def get_db():
    return psycopg2.connect(**settings.DB_CONFIG)

router = APIRouter()

# =========================================================
# OpenSearch Sparse Model Config
# =========================================================

OPENSEARCH_SPARSE_MODEL_ID = os.getenv(
    "OPENSEARCH_SPARSE_MODEL_ID",
    "opensearch-project/opensearch-neural-sparse-encoding-doc-v2-mini"
)


_opensearch_sparse_model = None
_opensearch_sparse_tokenizer = None
_opensearch_sparse_special_token_ids = None
_opensearch_sparse_id_to_token = None

def _load_opensearch_sparse_model():
    """
    Lazy load HuggingFace OpenSearch sparse encoder
    """
    global _opensearch_sparse_model
    global _opensearch_sparse_tokenizer
    global _opensearch_sparse_special_token_ids
    global _opensearch_sparse_id_to_token

    if _opensearch_sparse_model is not None:
        return (
            _opensearch_sparse_model,
            _opensearch_sparse_tokenizer,
            _opensearch_sparse_special_token_ids,
            _opensearch_sparse_id_to_token,
        )

    tokenizer = AutoTokenizer.from_pretrained(OPENSEARCH_SPARSE_MODEL_ID)
    model = AutoModelForMaskedLM.from_pretrained(OPENSEARCH_SPARSE_MODEL_ID)
    model.eval()

    special_token_ids = [
        tokenizer.vocab[token]
        for token in tokenizer.special_tokens_map.values()
        if token in tokenizer.vocab
    ]

    id_to_token = [""] * tokenizer.vocab_size
    for token, idx in tokenizer.vocab.items():
        id_to_token[idx] = token

    _opensearch_sparse_model = model
    _opensearch_sparse_tokenizer = tokenizer
    _opensearch_sparse_special_token_ids = special_token_ids
    _opensearch_sparse_id_to_token = id_to_token

    return model, tokenizer, special_token_ids, id_to_token


# =========================================================
# Sparse Embedding Generator
# =========================================================

def generate_sparse_embedding(text: str) -> dict:
    """
    Generate sparse embedding dạng:
    {
        "token": weight,
        ...
    }
    """
    if not text:
        return {}

    model, tokenizer, special_ids, id_to_token = _load_opensearch_sparse_model()

    with torch.no_grad():
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )
        outputs = model(**inputs)

        # logits: (seq_len, vocab_size)
        logits = outputs.logits[0]
        weights = torch.max(logits, dim=0).values

    sparse_embedding = {}
    for idx, score in enumerate(weights):
        if idx in special_ids:
            continue

        val = float(score)
        if val > 0:
            token = id_to_token[idx]
            sparse_embedding[token] = val

    return sparse_embedding


# =========================================================
# API: Generate Product Embeddings
# =========================================================

@router.post("/generate-embeddings")
def generate_product_embeddings():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT headcode, product_name, category, sub_category, material_primary
        FROM products_sparse
        WHERE name_embedding IS NULL OR description_embedding IS NULL
        LIMIT 100
    """)

    products = cur.fetchall()

    if not products:
        conn.close()
        return {"message": "✅ Tất cả products đã có embeddings"}

    success = 0
    errors = []

    for prod in products:
        try:
            name_text = prod["product_name"]
            desc_text = f"""
                {prod.get('product_name', '')}
                {prod.get('category', '')}
                {prod.get('sub_category', '')}
                {prod.get('material_primary', '')}
            """

            name_emb = generate_sparse_embedding(name_text)
            desc_emb = generate_sparse_embedding(desc_text)

            if name_emb and desc_emb:
                cur.execute("""
                    UPDATE products_sparse
                    SET
                        name_embedding = %s,
                        description_embedding = %s,
                        updated_at = NOW()
                    WHERE headcode = %s
                """, (
                    name_emb,
                    desc_emb,
                    prod["headcode"]
                ))

                success += 1
                time.sleep(0.2)

        except Exception as e:
            errors.append(f"{prod['headcode']}: {str(e)}")

    conn.commit()
    conn.close()

    return {
        "message": f"✅ Đã tạo embeddings cho {success}/{len(products)} products",
        "success": success,
        "total": len(products),
        "errors": errors[:5]
    }


# =========================================================
# API: Generate Material Embeddings
# =========================================================

@router.post("/generate-material-embeddings")
def generate_material_embeddings():
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT id_sap, material_name, material_group, material_subgroup
        FROM materials_sparse
        WHERE name_embedding IS NULL OR description_embedding IS NULL
        LIMIT 100
    """)

    materials = cur.fetchall()

    if not materials:
        conn.close()
        return {"message": "✅ Tất cả materials đã có embeddings"}

    success = 0
    errors = []

    for mat in materials:
        try:
            name_text = mat["material_name"]
            desc_text = f"""
                {mat.get('material_name', '')}
                {mat.get('material_group', '')}
                {mat.get('material_subgroup', '')}
            """

            name_emb = generate_sparse_embedding(name_text)
            desc_emb = generate_sparse_embedding(desc_text)

            if name_emb and desc_emb:
                cur.execute("""
                    UPDATE materials_sparse
                    SET
                        name_embedding = %s,
                        description_embedding = %s,
                        updated_at = NOW()
                    WHERE id_sap = %s
                """, (
                    name_emb,
                    desc_emb,
                    mat["id_sap"]
                ))

                success += 1
                time.sleep(0.2)

        except Exception as e:
            errors.append(f"{mat['id_sap']}: {str(e)}")

    conn.commit()
    conn.close()

    return {
        "message": f"✅ Đã tạo embeddings cho {success}/{len(materials)} materials",
        "success": success,
        "total": len(materials),
        "errors": errors[:5]
    }
