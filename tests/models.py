from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from sqlalchemy_oso_cloud.orm import Resource, relation, attribute

class Base(DeclarativeBase):
  pass

# TODO: figure out a pattern for referring to remote resources --
# ideally, we'd have a way to refer to Organization as a relation that Oso can pick up on,
# even if it doesn't live in a local table.
class Organization(Base, Resource):
  __tablename__ = "organization"
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str]
  documents: Mapped[list["Document"]] = relationship(back_populates="organization")

class Document(Base, Resource):
  __tablename__ = "document"
  id: Mapped[int] = mapped_column(primary_key=True)
  organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id"))
  # TODO: how do relationships work when there is no foreign key?
  organization: Mapped["Organization"] = relation(back_populates="documents")
  content: Mapped[str]
  status: Mapped[str] = attribute()
