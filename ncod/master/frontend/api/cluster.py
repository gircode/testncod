"""
Cluster API Router
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from ..config.dev import DATABASE_CONFIG
from ..database.db import DatabaseManager
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/clusters", tags=["clusters"])
db = DatabaseManager(DATABASE_CONFIG)


@router.get("")
async def list_clusters(
    status: Optional[str] = None, current_user: Dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """获取集群列表"""
    query = """
        SELECT 
            c.id,
            c.name,
            c.status,
            c.created_at,
            c.updated_at,
            COUNT(n.id) as node_count,
            MAX(n.last_heartbeat) as last_heartbeat
        FROM clusters c
        LEFT JOIN nodes n ON c.id = n.cluster_id
        WHERE ($1::text IS NULL OR c.status = $1)
        GROUP BY c.id
        ORDER BY c.created_at DESC
    """
    return await db.fetch(query, status)


@router.get("/{cluster_id}")
async def get_cluster(
    cluster_id: str, current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取集群详情"""
    query = """
        SELECT 
            c.*,
            json_agg(n.*) as nodes,
            (
                SELECT json_agg(m.*)
                FROM metrics m
                WHERE m.cluster_id = c.id
                AND m.created_at >= NOW() - INTERVAL '24 hours'
            ) as metrics
        FROM clusters c
        LEFT JOIN nodes n ON c.id = n.cluster_id
        WHERE c.id = $1
        GROUP BY c.id
    """
    cluster = await db.fetchrow(query, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return dict(cluster)


@router.post("")
async def create_cluster(
    cluster: Dict[str, Any], current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """创建新集群"""
    query = """
        INSERT INTO clusters (name, description, config)
        VALUES ($1, $2, $3)
        RETURNING *
    """
    return dict(
        await db.fetchrow(
            query,
            cluster["name"],
            cluster.get("description"),
            cluster.get("config", {}),
        )
    )


@router.put("/{cluster_id}")
async def update_cluster(
    cluster_id: str,
    cluster: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """更新集群信息"""
    query = """
        UPDATE clusters
        SET 
            name = $2,
            description = $3,
            config = $4,
            updated_at = NOW()
        WHERE id = $1
        RETURNING *
    """
    updated = await db.fetchrow(
        query,
        cluster_id,
        cluster["name"],
        cluster.get("description"),
        cluster.get("config", {}),
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return dict(updated)


@router.delete("/{cluster_id}")
async def delete_cluster(
    cluster_id: str, current_user: Dict = Depends(get_current_user)
) -> Dict[str, str]:
    """删除集群"""
    query = "DELETE FROM clusters WHERE id = $1 RETURNING id"
    deleted = await db.fetchval(query, cluster_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return {"message": "Cluster deleted successfully"}


@router.post("/{cluster_id}/nodes")
async def add_node(
    cluster_id: str,
    node: Dict[str, Any],
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """添加节点到集群"""
    query = """
        INSERT INTO nodes (cluster_id, name, address, type, config)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
    """
    return dict(
        await db.fetchrow(
            query,
            cluster_id,
            node["name"],
            node["address"],
            node["type"],
            node.get("config", {}),
        )
    )


@router.delete("/{cluster_id}/nodes/{node_id}")
async def remove_node(
    cluster_id: str, node_id: str, current_user: Dict = Depends(get_current_user)
) -> Dict[str, str]:
    """从集群移除节点"""
    query = """
        DELETE FROM nodes 
        WHERE id = $1 AND cluster_id = $2
        RETURNING id
    """
    deleted = await db.fetchval(query, node_id, cluster_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": "Node removed successfully"}
