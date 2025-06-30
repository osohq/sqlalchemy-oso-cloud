# SQLAlchemy 🤝 Oso Cloud

The Oso Cloud extension for SQLAlchemy enables you to filter database
queries based on your application's authorization logic.

- With Local Authorization, you don’t need all your data in one place.
  Let your other services own things like user roles and entitlements. We’ll stitch
  anything relevant into queries over your SQLAlchemy data, with no need to
  sync.
- Pair with other extensions like `pgvector` to build powerful, secure RAG search over private data.
- First-class SQLAlchemy support for unparalleled ergonomics.

## Install

```bash
pip install sqlalchemy-oso-cloud
```

## Use

### Step 1: Map SQLAlchemy Data

With the utilities in [sqlalchemy_oso_cloud.orm], bind
data in your SQLAlchemy models to the Oso facts you'll use
in your authorization policy.

```python
import sqlalchemy_oso_cloud as oso

class Document(Base, oso.Resource):
    ...
    # TODO(iris): decide on this API
    organization: relation(remote="Organization")
    # maps facts like `has_state(Document{"123"}, "published")`
    state: Mapped[str] = oso.attribute()

class DocumentChunk(Base, oso.Resource):
    ...
    # maps facts like `has_relation(DocumentChunk{"456"}, "document", Document{"123"})`
    document: Mapped["Document"] = oso.relation()
```

### Step 2: Write a Polar policy

Unlike SQLAlchemy models which are specific to one database,
Polar is agnostic of where each piece of data comes from.

```polar
actor User {}

resource Organization {
    roles = ["admin", "member"];
}

resource Document {
    roles = ["author"];
    permissions = ["read", "write"];
    relations = {
      organization: Organization
    };

    "read" if "author";
    "read" if "admin" on "organization";
    "read" if
        "member" on "organization" and
        has_state(resource, "published");

    "write" if "author";
}

resource DocumentChunk {
    permissions = ["read"];
    relations = {
        document: Document
    };

    "read" if "read" on "document";
}
```

### Step 3: Profit

```python
from .models import Base, DocumentChunk
import sqlalchemy_oso_cloud

sqlalchemy_oso_cloud.init(Base.registry)

def authorized_rag_retrieval(user, embedding):
    return select(DocumentChunk)
        .order_by(DocumentChunk.embedding.l2_distance(embedding))
        .authorized(user, "read")
        .limit(10)
```

# Reference

- [API Reference](https://osohq.github.io/sqlalchemy-oso-cloud)
- [Oso Cloud](https://www.osohq.com/docs)
  - [Polar](https://www.osohq.com/docs/modeling-in-polar)
  - [Local Authorization](https://www.osohq.com/docs/authorization-data/local-authorization)
  - [Python SDK](https://www.osohq.com/docs/app-integration/client-apis/python)
- [SQLAlchemy](https://docs.sqlalchemy.org/)

## Slack

[Join our Slack community](https://join-slack.osohq.com/) where Oso users and developers
hang out! It's a great place to ask questions, share feedback, and get advice.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

[Apache 2.0](LICENSE)
