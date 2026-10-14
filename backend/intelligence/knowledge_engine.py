"""
Agy Studio v2.6 — Knowledge Engine
Lightweight SQLite Knowledge Graph for entities and verified relations.
"""

import time
import json
import sqlite3
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional
from .confidence_engine import ConfidenceLevel

class KnowledgeEntity:
    def __init__(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
        confidence: str = ConfidenceLevel.OBSERVED.value,
        created_at: Optional[str] = None
    ):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.name = name
        self.properties = properties or {}
        self.confidence = confidence
        self.created_at = created_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "name": self.name,
            "properties": self.properties,
            "confidence": self.confidence,
            "created_at": self.created_at
        }

class KnowledgeRelation:
    def __init__(
        self,
        relation_id: str,
        from_entity_id: str,
        relation_type: str,
        to_entity_id: str,
        weight: float = 1.0,
        evidence_refs: Optional[List[str]] = None,
        created_at: Optional[str] = None
    ):
        self.relation_id = relation_id
        self.from_entity_id = from_entity_id
        self.relation_type = relation_type
        self.to_entity_id = to_entity_id
        self.weight = weight
        self.evidence_refs = evidence_refs or []
        self.created_at = created_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "from_entity_id": self.from_entity_id,
            "relation_type": self.relation_type,
            "to_entity_id": self.to_entity_id,
            "weight": round(self.weight, 2),
            "evidence_refs": self.evidence_refs,
            "created_at": self.created_at
        }

class KnowledgeEngine:
    """Manages entities and relations in SQLite tables."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_entities (
                    entity_id TEXT PRIMARY KEY,
                    entity_type TEXT,
                    name TEXT,
                    properties TEXT,
                    confidence TEXT,
                    created_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ke_type ON knowledge_entities(entity_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ke_name ON knowledge_entities(name)")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_relations (
                    relation_id TEXT PRIMARY KEY,
                    from_entity_id TEXT,
                    relation_type TEXT,
                    to_entity_id TEXT,
                    weight REAL,
                    evidence_refs TEXT,
                    created_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_kr_from ON knowledge_relations(from_entity_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_kr_to ON knowledge_relations(to_entity_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_kr_type ON knowledge_relations(relation_type)")

    def add_entity(
        self,
        entity_type: str,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
        confidence: str = ConfidenceLevel.OBSERVED.value,
        entity_id: Optional[str] = None
    ) -> KnowledgeEntity:
        eid = entity_id or f"ENT-{entity_type[:3].upper()}-{secrets.token_hex(4).upper()}"
        props = properties or {}
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with self._get_conn() as conn:
            # Check if exists with same name & type
            existing = conn.execute(
                "SELECT * FROM knowledge_entities WHERE entity_type = ? AND LOWER(name) = LOWER(?)",
                (entity_type, name.strip())
            ).fetchone()
            if existing:
                eid = existing["entity_id"]
                conn.execute("""
                    UPDATE knowledge_entities SET properties = ?, confidence = ? WHERE entity_id = ?
                """, (json.dumps(props, ensure_ascii=False), confidence, eid))
            else:
                conn.execute("""
                    INSERT INTO knowledge_entities (entity_id, entity_type, name, properties, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (eid, entity_type, name.strip(), json.dumps(props, ensure_ascii=False), confidence, now_iso))

        return KnowledgeEntity(eid, entity_type, name.strip(), props, confidence, now_iso)

    def add_relation(
        self,
        from_entity_id: str,
        relation_type: str,
        to_entity_id: str,
        weight: float = 1.0,
        evidence_ref: Optional[str] = None
    ) -> KnowledgeRelation:
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rid = f"REL-{relation_type[:4].upper()}-{secrets.token_hex(4).upper()}"
        ev = [evidence_ref] if evidence_ref else []
        with self._get_conn() as conn:
            existing = conn.execute("""
                SELECT * FROM knowledge_relations
                WHERE from_entity_id = ? AND relation_type = ? AND to_entity_id = ?
            """, (from_entity_id, relation_type, to_entity_id)).fetchone()
            if existing:
                rid = existing["relation_id"]
                prev_ev = json.loads(existing["evidence_refs"]) if existing["evidence_refs"] else []
                if evidence_ref and evidence_ref not in prev_ev:
                    prev_ev.append(evidence_ref)
                new_weight = existing["weight"] + 0.5
                conn.execute("""
                    UPDATE knowledge_relations SET weight = ?, evidence_refs = ? WHERE relation_id = ?
                """, (new_weight, json.dumps(prev_ev, ensure_ascii=False), rid))
                return KnowledgeRelation(rid, from_entity_id, relation_type, to_entity_id, new_weight, prev_ev, existing["created_at"])
            else:
                conn.execute("""
                    INSERT INTO knowledge_relations (relation_id, from_entity_id, relation_type, to_entity_id, weight, evidence_refs, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (rid, from_entity_id, relation_type, to_entity_id, weight, json.dumps(ev, ensure_ascii=False), now_iso))
                return KnowledgeRelation(rid, from_entity_id, relation_type, to_entity_id, weight, ev, now_iso)

    def query_relations_from(self, entity_id: str, relation_type: Optional[str] = None) -> List[KnowledgeRelation]:
        query = "SELECT * FROM knowledge_relations WHERE from_entity_id = ?"
        params: List[Any] = [entity_id]
        if relation_type:
            query += " AND relation_type = ?"
            params.append(relation_type)
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                KnowledgeRelation(
                    r["relation_id"], r["from_entity_id"], r["relation_type"],
                    r["to_entity_id"], r["weight"],
                    json.loads(r["evidence_refs"]) if r["evidence_refs"] else [],
                    r["created_at"]
                ) for r in rows
            ]

    def export_graph_json(self) -> Dict[str, Any]:
        with self._get_conn() as conn:
            e_rows = conn.execute("SELECT * FROM knowledge_entities").fetchall()
            r_rows = conn.execute("SELECT * FROM knowledge_relations").fetchall()

            entities = []
            for r in e_rows:
                entities.append({
                    "entity_id": r["entity_id"],
                    "entity_type": r["entity_type"],
                    "name": r["name"],
                    "properties": json.loads(r["properties"]) if r["properties"] else {},
                    "confidence": r["confidence"],
                    "created_at": r["created_at"]
                })

            relations = []
            for r in r_rows:
                relations.append({
                    "relation_id": r["relation_id"],
                    "from_entity_id": r["from_entity_id"],
                    "relation_type": r["relation_type"],
                    "to_entity_id": r["to_entity_id"],
                    "weight": r["weight"],
                    "evidence_refs": json.loads(r["evidence_refs"]) if r["evidence_refs"] else [],
                    "created_at": r["created_at"]
                })

            return {
                "version": "2.6.0",
                "total_entities": len(entities),
                "total_relations": len(relations),
                "entities": entities,
                "relations": relations
            }
