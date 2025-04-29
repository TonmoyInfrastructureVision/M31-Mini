import logging
from typing import List, Dict, Any, Optional, Union
import os
from datetime import datetime
import uuid

from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config.settings import settings

logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
engine = create_engine(
    settings.db.url,
    connect_args=settings.db.connect_args,
    echo=settings.db.echo
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    model = Column(String, nullable=True)
    workspace_dir = Column(String, nullable=False)
    status = Column(String, nullable=False, default="idle")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    config = Column(JSON, nullable=True)


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, index=True, nullable=False)
    goal = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    plan = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True)
    reflection = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)


def get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


class Database:
    def __init__(self):
        self.initialized = False
        self.engine = None
        
    def initialize(self) -> None:
        if self.initialized:
            return
            
        logger.info(f"Initializing database with settings: {settings.db}")
        
        try:
            # Make sure tables exist
            Base.metadata.create_all(bind=engine)
            self.initialized = True
            self.engine = engine
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
            
    def _get_session(self) -> Session:
        return SessionLocal()
        
    def create_agent(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.initialized:
            self.initialize()
            
        session = self._get_session()
        try:
            agent_id = data.get("id", str(uuid.uuid4()))
            
            # Create workspace directory if it doesn't exist
            workspace_dir = data.get("workspace_dir")
            if not workspace_dir:
                workspace_dir = os.path.join(settings.agent.workspace_root, agent_id)
                data["workspace_dir"] = workspace_dir
                
            os.makedirs(workspace_dir, exist_ok=True)
            
            # Create agent
            agent = Agent(
                id=agent_id,
                name=data["name"],
                description=data.get("description"),
                model=data.get("model", settings.agent.default_model),
                workspace_dir=workspace_dir,
                status="idle",
                config=data.get("config", {}),
            )
            
            session.add(agent)
            session.commit()
            session.refresh(agent)
            
            return self._agent_to_dict(agent)
        finally:
            session.close()
            
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        session = self._get_session()
        try:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            
            if not agent:
                return None
                
            return self._agent_to_dict(agent)
        finally:
            session.close()
            
    def get_agents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        session = self._get_session()
        try:
            agents = session.query(Agent).order_by(Agent.created_at.desc()).offset(offset).limit(limit).all()
            
            return [self._agent_to_dict(agent) for agent in agents]
        finally:
            session.close()
            
    def update_agent(self, agent_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        session = self._get_session()
        try:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            
            if not agent:
                return None
                
            # Update agent fields
            for key, value in data.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
                    
            agent.updated_at = datetime.utcnow()
            
            session.commit()
            session.refresh(agent)
            
            return self._agent_to_dict(agent)
        finally:
            session.close()
            
    def delete_agent(self, agent_id: str) -> bool:
        if not self.initialized:
            self.initialize()
            
        session = self._get_session()
        try:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            
            if not agent:
                return False
                
            session.delete(agent)
            session.commit()
            
            return True
        finally:
            session.close()
            
    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.initialized:
            self.initialize()
            
        session = self._get_session()
        try:
            task_id = data.get("id", str(uuid.uuid4()))
            
            task = Task(
                id=task_id,
                agent_id=data["agent_id"],
                goal=data["goal"],
                status="pending",
            )
            
            session.add(task)
            session.commit()
            session.refresh(task)
            
            return self._task_to_dict(task)
        finally:
            session.close()
            
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        session = self._get_session()
        try:
            task = session.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                return None
                
            return self._task_to_dict(task)
        finally:
            session.close()
            
    def get_agent_tasks(self, agent_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        session = self._get_session()
        try:
            tasks = (
                session.query(Task)
                .filter(Task.agent_id == agent_id)
                .order_by(Task.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            
            return [self._task_to_dict(task) for task in tasks]
        finally:
            session.close()
            
    def update_task(self, task_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        session = self._get_session()
        try:
            task = session.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                return None
                
            # Update task fields
            for key, value in data.items():
                if hasattr(task, key):
                    setattr(task, key, value)
                    
            # Handle special case for completed status
            if data.get("status") == "completed" and task.completed_at is None:
                task.completed_at = datetime.utcnow()
                
            task.updated_at = datetime.utcnow()
            
            session.commit()
            session.refresh(task)
            
            return self._task_to_dict(task)
        finally:
            session.close()
            
    def _agent_to_dict(self, agent: Agent) -> Dict[str, Any]:
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "model": agent.model,
            "workspace_dir": agent.workspace_dir,
            "status": agent.status,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat(),
            "config": agent.config,
        }
        
    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        result = {
            "id": task.id,
            "agent_id": task.agent_id,
            "goal": task.goal,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "plan": task.plan,
            "results": task.results,
            "reflection": task.reflection,
            "error": task.error,
        }
        
        if task.completed_at:
            result["completed_at"] = task.completed_at.isoformat()
            
        return result


# Create singleton instance
db = Database() 