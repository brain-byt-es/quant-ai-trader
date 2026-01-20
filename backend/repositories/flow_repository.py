from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from database.models import HedgeFundFlow


class FlowRepository:
    """Repository for HedgeFundFlow CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_flow(
        self, 
        name: str, 
        nodes: List[Dict[str, Any]], 
        edges: List[Dict[str, Any]], 
        description: Optional[str] = None, 
        viewport: Optional[Dict[str, Any]] = None, 
        data: Optional[Dict[str, Any]] = None, 
        is_template: bool = False, 
        tags: Optional[List[str]] = None
    ) -> HedgeFundFlow:
        """Create a new hedge fund flow"""
        flow = HedgeFundFlow(
            name=name, 
            description=description, 
            nodes=nodes, 
            edges=edges, 
            viewport=viewport, 
            data=data, 
            is_template=is_template, 
            tags=tags or []
        )
        self.db.add(flow)
        self.db.commit()
        self.db.refresh(flow)
        return flow

    def get_flow_by_id(self, flow_id: int) -> Optional[HedgeFundFlow]:
        """Get a flow by its ID"""
        return self.db.query(HedgeFundFlow).filter(HedgeFundFlow.id == flow_id).first()

    def get_all_flows(self, include_templates: bool = True) -> List[HedgeFundFlow]:
        """Get all flows, optionally excluding templates"""
        query = self.db.query(HedgeFundFlow)
        if not include_templates:
            query = query.filter(HedgeFundFlow.is_template.is_(False))
        return query.order_by(desc(HedgeFundFlow.updated_at)).all()

    def get_flows_by_name(self, name: str) -> List[HedgeFundFlow]:
        """Search flows by name (case-insensitive partial match)"""
        return self.db.query(HedgeFundFlow).filter(HedgeFundFlow.name.ilike(f"%{name}%")).order_by(desc(HedgeFundFlow.updated_at)).all()

    def update_flow(
        self, 
        flow_id: int, 
        name: Optional[str] = None, 
        description: Optional[str] = None, 
        nodes: Optional[List[Dict[str, Any]]] = None, 
        edges: Optional[List[Dict[str, Any]]] = None, 
        viewport: Optional[Dict[str, Any]] = None, 
        data: Optional[Dict[str, Any]] = None, 
        is_template: Optional[bool] = None, 
        tags: Optional[List[str]] = None
    ) -> Optional[HedgeFundFlow]:
        """Update an existing flow"""
        flow = self.get_flow_by_id(flow_id)
        if not flow:
            return None

        if name is not None:
            flow.name = name
        if description is not None:
            flow.description = description
        if nodes is not None:
            flow.nodes = nodes
        if edges is not None:
            flow.edges = edges
        if viewport is not None:
            flow.viewport = viewport
        if data is not None:
            flow.data = data
        if is_template is not None:
            flow.is_template = is_template
        if tags is not None:
            flow.tags = tags

        self.db.commit()
        self.db.refresh(flow)
        return flow

    def delete_flow(self, flow_id: int) -> bool:
        """Delete a flow by ID"""
        flow = self.get_flow_by_id(flow_id)
        if not flow:
            return False

        self.db.delete(flow)
        self.db.commit()
        return True

    def duplicate_flow(self, flow_id: int, new_name: Optional[str] = None) -> Optional[HedgeFundFlow]:
        """Create a copy of an existing flow"""
        original = self.get_flow_by_id(flow_id)
        if not original:
            return None

        copy_name = new_name or f"{original.name} (Copy)"

        return self.create_flow(
            name=copy_name, 
            description=str(original.description), 
            nodes=list(original.nodes), 
            edges=list(original.edges), 
            viewport=dict(original.viewport) if original.viewport else None, 
            data=dict(original.data) if original.data else None, 
            is_template=False, 
            tags=list(original.tags) if original.tags else None
        )
