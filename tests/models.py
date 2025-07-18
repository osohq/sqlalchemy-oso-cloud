from datetime import datetime
from pgvector.sqlalchemy import Vector # type: ignore
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String
from sqlalchemy_oso_cloud.orm import Resource, HasRole, relation, attribute, remote_relation

class Base(DeclarativeBase):
  pass

class Organization(Base, Resource):
  __tablename__ = "organization"
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str]
  documents: Mapped[list["Document"]] = relation(back_populates="organization")

class AgentOrganizationRole(Base, HasRole):
  __tablename__ = "agent_organization_role"
  id: Mapped[int] = mapped_column(primary_key=True)
  agent_id: Mapped[int] = HasRole.actor(ForeignKey("agent.id"))
  organization_id: Mapped[int] = HasRole.resource(ForeignKey("organization.id"))
  role_id: Mapped[str] = HasRole.role(String(50))
  granted_at: Mapped[datetime] = mapped_column(default=datetime.now)
  agent: Mapped["Agent"] = relationship()
  organization: Mapped["Organization"] = relationship()

class Agent(Base, Resource):
  __tablename__ = "agent"
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str]
  organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id"))
  organization: Mapped["Organization"] = relation()

class Document(Base, Resource):
  __tablename__ = "document"
  id: Mapped[int] = mapped_column(primary_key=True)
  organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id"))
  organization: Mapped["Organization"] = relation(back_populates="documents")
  team_id: Mapped[int] = remote_relation(remote_resource_name="Team")
  content: Mapped[str]
  status: Mapped[str] = attribute()
  is_public: Mapped[bool] = attribute(default=False)
  embedding: Mapped[list[float]] = mapped_column(Vector(3), nullable=True)
