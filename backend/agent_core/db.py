import logging
from typing import List, Dict, Any, Optional, Union, TypeVar, Generic, Type, Callable, Awaitable
import os
from datetime import datetime
import uuid
import json
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON, Boolean, Integer, ForeignKey, Enum, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, scoped_session
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
from alembic.config import Config
from alembic import command

from config.settings import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Initialize SQLAlchemy with connection pooling
engine = create_engine(
    settings.db.url,
    connect_args=settings.db.connect_args,
    echo=settings.db.echo,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
    pool_timeout=settings.db.pool_timeout,
    poolclass=QueuePool
)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()


class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    model = Column(String(255), nullable=True)
    workspace_dir = Column(String(512), nullable=False)
    status = Column(String(50), nullable=False, default="idle")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    config = Column(JSON, nullable=True)
    max_iterations = Column(Integer, default=10)
    temperature = Column(Float, default=0.7)
    active = Column(Boolean, default=True)
    
    tasks = relationship("Task", back_populates="agent", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_agent_name', name),
        Index('idx_agent_status', status),
        Index('idx_agent_active', active),
    )


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True, index=True)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    goal = Column(Text, nullable=False)
    status = Column(Enum("pending", "running", "completed", "failed", "cancelled", name="task_status"), 
                   nullable=False, default="pending")
    priority = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    plan = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True)
    reflection = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    
    agent = relationship("Agent", back_populates="tasks")
    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_task_agent_id', agent_id),
        Index('idx_task_status', status),
        Index('idx_task_priority', priority),
        Index('idx_task_scheduled_for', scheduled_for),
    )


class TaskStep(Base):
    __tablename__ = "task_steps"
    
    id = Column(String(36), primary_key=True, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer, nullable=False)
    action = Column(Text, nullable=False)
    tool = Column(String(255), nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    status = Column(Enum("pending", "running", "completed", "failed", name="step_status"), 
                   nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    
    task = relationship("Task", back_populates="steps")

    __table_args__ = (
        Index('idx_step_task_id', task_id),
        Index('idx_step_number', step_number),
        Index('idx_step_status', status),
    )


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    api_key = Column(String(255), unique=True, nullable=True)
    
    __table_args__ = (
        Index('idx_user_is_active', is_active),
    )


class ToolExecution(Base):
    __tablename__ = "tool_executions"
    
    id = Column(String(36), primary_key=True, index=True)
    task_step_id = Column(String(36), ForeignKey("task_steps.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(255), nullable=False)
    inputs = Column(JSON, nullable=True)
    outputs = Column(JSON, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default="success")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    error = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_tool_execution_task_step', task_step_id),
        Index('idx_tool_execution_tool_name', tool_name),
    )


@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        session.close()


def get_db() -> Session:
    session = SessionLocal()
    try:
        return session
    finally:
        session.close()


class ModelCRUD(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model
    
    def create(self, session: Session, data: Dict[str, Any]) -> T:
        obj = self.model(**data)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj
    
    def get(self, session: Session, id: str) -> Optional[T]:
        return session.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, session: Session, skip: int = 0, limit: int = 100) -> List[T]:
        return session.query(self.model).offset(skip).limit(limit).all()
    
    def update(self, session: Session, id: str, data: Dict[str, Any]) -> Optional[T]:
        obj = session.query(self.model).filter(self.model.id == id).first()
        if not obj:
            return None
        
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        
        session.commit()
        session.refresh(obj)
        return obj
    
    def delete(self, session: Session, id: str) -> bool:
        obj = session.query(self.model).filter(self.model.id == id).first()
        if not obj:
            return False
        
        session.delete(obj)
        session.commit()
        return True


class Database:
    def __init__(self):
        self.initialized = False
        self.engine = None
        self.agent_crud = ModelCRUD(Agent)
        self.task_crud = ModelCRUD(Task)
        self.task_step_crud = ModelCRUD(TaskStep)
        self.user_crud = ModelCRUD(User)
        self.tool_execution_crud = ModelCRUD(ToolExecution)
        
    def initialize(self) -> None:
        if self.initialized:
            return
            
        logger.info(f"Initializing database with settings: {settings.db}")
        
        try:
            # Make sure tables exist
            Base.metadata.create_all(bind=engine)
            self.initialized = True
            self.engine = engine
            
            # Run migrations if enabled
            if settings.db.run_migrations:
                self._run_migrations()
                
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def _run_migrations(self) -> None:
        try:
            logger.info("Running database migrations")
            alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
            alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "migrations"))
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.error(f"Error running migrations: {str(e)}")
            raise
    
    def backup(self, backup_path: str) -> bool:
        if not self.initialized:
            self.initialize()
        
        try:
            logger.info(f"Creating database backup at {backup_path}")
            
            with get_db_session() as session:
                # Export agents
                agents = session.query(Agent).all()
                agent_data = [self._agent_to_dict(agent) for agent in agents]
                
                # Export tasks
                tasks = session.query(Task).all()
                task_data = [self._task_to_dict(task) for task in tasks]
                
                # Export task steps
                task_steps = session.query(TaskStep).all()
                task_step_data = []
                for step in task_steps:
                    step_dict = {c.name: getattr(step, c.name) for c in step.__table__.columns}
                    step_dict = self._serialize_datetime_fields(step_dict)
                    task_step_data.append(step_dict)
                
                # Export users
                users = session.query(User).all()
                user_data = []
                for user in users:
                    user_dict = {c.name: getattr(user, c.name) for c in user.__table__.columns}
                    user_dict = self._serialize_datetime_fields(user_dict)
                    user_data.append(user_dict)
                
                # Export tool executions
                tool_execs = session.query(ToolExecution).all()
                tool_exec_data = []
                for exec in tool_execs:
                    exec_dict = {c.name: getattr(exec, c.name) for c in exec.__table__.columns}
                    exec_dict = self._serialize_datetime_fields(exec_dict)
                    tool_exec_data.append(exec_dict)
                
                # Create backup data
                backup_data = {
                    "version": "1.0",
                    "timestamp": datetime.utcnow().isoformat(),
                    "agents": agent_data,
                    "tasks": task_data,
                    "task_steps": task_step_data,
                    "users": user_data,
                    "tool_executions": tool_exec_data
                }
                
                # Save to file
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                with open(backup_path, 'w') as f:
                    json.dump(backup_data, f, indent=2)
                
                logger.info(f"Database backup created successfully")
                return True
        except Exception as e:
            logger.error(f"Error creating database backup: {str(e)}")
            return False
    
    def restore(self, backup_path: str) -> bool:
        if not self.initialized:
            self.initialize()
        
        try:
            logger.info(f"Restoring database from backup at {backup_path}")
            
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            with get_db_session() as session:
                # Clear existing data (in reverse order of dependencies)
                session.query(ToolExecution).delete()
                session.query(TaskStep).delete()
                session.query(Task).delete()
                session.query(Agent).delete()
                session.query(User).delete()
                
                # Restore users
                for user_data in backup_data.get("users", []):
                    user = User(**user_data)
                    session.add(user)
                
                # Restore agents
                for agent_data in backup_data.get("agents", []):
                    agent = Agent(**agent_data)
                    session.add(agent)
                
                # Restore tasks
                for task_data in backup_data.get("tasks", []):
                    task = Task(**task_data)
                    session.add(task)
                
                # Restore task steps
                for step_data in backup_data.get("task_steps", []):
                    step = TaskStep(**step_data)
                    session.add(step)
                
                # Restore tool executions
                for exec_data in backup_data.get("tool_executions", []):
                    exec = ToolExecution(**exec_data)
                    session.add(exec)
                
                session.commit()
                logger.info(f"Database restore completed successfully")
                return True
        except Exception as e:
            logger.error(f"Error restoring database from backup: {str(e)}")
            return False
            
    def create_agent(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.initialized:
            self.initialize()
            
        with get_db_session() as session:
            agent_id = data.get("id", str(uuid.uuid4()))
            
            # Create workspace directory if it doesn't exist
            workspace_dir = data.get("workspace_dir")
            if not workspace_dir:
                workspace_dir = os.path.join(settings.agent.workspace_root, agent_id)
                data["workspace_dir"] = workspace_dir
                
            os.makedirs(workspace_dir, exist_ok=True)
            
            # Set defaults for new fields
            if "max_iterations" not in data:
                data["max_iterations"] = 10
            if "temperature" not in data:
                data["temperature"] = 0.7
            if "active" not in data:
                data["active"] = True
            
            # Create agent
            agent = Agent(
                id=agent_id,
                name=data["name"],
                description=data.get("description"),
                model=data.get("model", settings.agent.default_model),
                workspace_dir=workspace_dir,
                status="idle",
                config=data.get("config", {}),
                max_iterations=data.get("max_iterations", 10),
                temperature=data.get("temperature", 0.7),
                active=data.get("active", True)
            )
            
            session.add(agent)
            return self._agent_to_dict(agent)
            
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        with get_db_session() as session:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            
            if not agent:
                return None
                
            return self._agent_to_dict(agent)
            
    def get_agents(self, 
                  limit: int = 100, 
                  offset: int = 0, 
                  status: Optional[str] = None,
                  active_only: bool = True) -> List[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        with get_db_session() as session:
            query = session.query(Agent)
            
            if status:
                query = query.filter(Agent.status == status)
                
            if active_only:
                query = query.filter(Agent.active == True)
                
            agents = query.order_by(Agent.created_at.desc()).offset(offset).limit(limit).all()
            
            return [self._agent_to_dict(agent) for agent in agents]
            
    def update_agent(self, agent_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        with get_db_session() as session:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            
            if not agent:
                return None
                
            # Update agent fields
            for key, value in data.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
                    
            return self._agent_to_dict(agent)
            
    def delete_agent(self, agent_id: str) -> bool:
        if not self.initialized:
            self.initialize()
            
        with get_db_session() as session:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            
            if not agent:
                return False
                
            session.delete(agent)
            return True
            
    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.initialized:
            self.initialize()
            
        with get_db_session() as session:
            task_id = data.get("id", str(uuid.uuid4()))
            
            task = Task(
                id=task_id,
                agent_id=data["agent_id"],
                goal=data["goal"],
                status=data.get("status", "pending"),
                priority=data.get("priority", 1),
                scheduled_for=data.get("scheduled_for"),
                meta_data=data.get("meta_data", {})
            )
            
            session.add(task)
            return self._task_to_dict(task)
            
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        with get_db_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                return None
                
            return self._task_to_dict(task)
            
    def get_agent_tasks(self, 
                       agent_id: str, 
                       limit: int = 100, 
                       offset: int = 0,
                       status: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        with get_db_session() as session:
            query = session.query(Task).filter(Task.agent_id == agent_id)
            
            if status:
                query = query.filter(Task.status == status)
                
            tasks = query.order_by(Task.priority.desc(), Task.created_at.asc()).offset(offset).limit(limit).all()
            
            return [self._task_to_dict(task) for task in tasks]
            
    def update_task(self, task_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        with get_db_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                return None
                
            # Update task fields
            for key, value in data.items():
                if hasattr(task, key):
                    setattr(task, key, value)
                    
            # Update timestamps for status changes
            if "status" in data:
                if data["status"] == "running" and not task.started_at:
                    task.started_at = datetime.utcnow()
                elif data["status"] in ["completed", "failed"] and not task.completed_at:
                    task.completed_at = datetime.utcnow()
                    
            return self._task_to_dict(task)
    
    def create_task_step(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.initialized:
            self.initialize()
            
        with get_db_session() as session:
            step_id = data.get("id", str(uuid.uuid4()))
            
            step = TaskStep(
                id=step_id,
                task_id=data["task_id"],
                step_number=data["step_number"],
                action=data["action"],
                tool=data.get("tool"),
                input_data=data.get("input_data"),
                output_data=data.get("output_data"),
                status=data.get("status", "pending"),
            )
            
            session.add(step)
            step_dict = {c.name: getattr(step, c.name) for c in step.__table__.columns}
            return self._serialize_datetime_fields(step_dict)
    
    def get_task_steps(self, task_id: str) -> List[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        with get_db_session() as session:
            steps = session.query(TaskStep).filter(TaskStep.task_id == task_id).order_by(TaskStep.step_number).all()
            
            result = []
            for step in steps:
                step_dict = {c.name: getattr(step, c.name) for c in step.__table__.columns}
                step_dict = self._serialize_datetime_fields(step_dict)
                result.append(step_dict)
                
            return result
    
    def update_task_step(self, step_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.initialized:
            self.initialize()
            
        with get_db_session() as session:
            step = session.query(TaskStep).filter(TaskStep.id == step_id).first()
            
            if not step:
                return None
                
            # Update step fields
            for key, value in data.items():
                if hasattr(step, key):
                    setattr(step, key, value)
                    
            # Update timestamps for status changes
            if "status" in data:
                if data["status"] == "running" and not step.started_at:
                    step.started_at = datetime.utcnow()
                elif data["status"] in ["completed", "failed"] and not step.completed_at:
                    step.completed_at = datetime.utcnow()
                    
            step_dict = {c.name: getattr(step, c.name) for c in step.__table__.columns}
            return self._serialize_datetime_fields(step_dict)
    
    def log_tool_execution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.initialized:
            self.initialize()
            
        with get_db_session() as session:
            exec_id = data.get("id", str(uuid.uuid4()))
            
            exec = ToolExecution(
                id=exec_id,
                task_step_id=data["task_step_id"],
                tool_name=data["tool_name"],
                inputs=data.get("inputs"),
                outputs=data.get("outputs"),
                duration_ms=data.get("duration_ms"),
                status=data.get("status", "success"),
                error=data.get("error")
            )
            
            session.add(exec)
            exec_dict = {c.name: getattr(exec, c.name) for c in exec.__table__.columns}
            return self._serialize_datetime_fields(exec_dict)
            
    def _agent_to_dict(self, agent: Agent) -> Dict[str, Any]:
        agent_dict = {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "model": agent.model,
            "workspace_dir": agent.workspace_dir,
            "status": agent.status,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
            "config": agent.config,
            "max_iterations": agent.max_iterations,
            "temperature": agent.temperature,
            "active": agent.active
        }
        
        return agent_dict
            
    def _task_to_dict(self, task: Task) -> Dict[str, Any]:
        task_dict = {
            "id": task.id,
            "agent_id": task.agent_id,
            "goal": task.goal,
            "status": task.status,
            "priority": task.priority,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "plan": task.plan,
            "results": task.results,
            "reflection": task.reflection,
            "error": task.error,
            "meta_data": task.meta_data,
            "scheduled_for": task.scheduled_for.isoformat() if task.scheduled_for else None,
        }
        
        return task_dict
    
    def _serialize_datetime_fields(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in data_dict.items():
            if isinstance(value, datetime):
                data_dict[key] = value.isoformat()
        return data_dict


# Singleton instance
db = Database() 