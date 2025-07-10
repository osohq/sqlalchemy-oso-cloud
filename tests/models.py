from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String
from sqlalchemy_oso_cloud.orm import Resource, RoleMapping, actor, relation, attribute, remote_relation, resource, role

class Base(DeclarativeBase):
  pass

class Organization(Base, Resource):
  __tablename__ = "organization"
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str]
  documents: Mapped[list["Document"]] = relation(back_populates="organization")

class Role(Base, Resource):
  __tablename__ = "role"
  id: Mapped[str] = mapped_column(String(50), primary_key=True)
  description: Mapped[str]

class AgentOrganizationRole(Base, Resource, RoleMapping):
  __tablename__ = "agent_organization_role"
  id: Mapped[int] = mapped_column(primary_key=True)
  agent_id: Mapped[int] = actor(ForeignKey("agent.id"))
  organization_id: Mapped[int] = resource(ForeignKey("organization.id"))
  role_id: Mapped[str] = role(String(50), ForeignKey("role.id"))
  granted_at: Mapped[datetime] = mapped_column(default=datetime.now)
  agent: Mapped["Agent"] = relationship()
  organization: Mapped["Organization"] = relationship()
  role: Mapped["Role"] = relationship()

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