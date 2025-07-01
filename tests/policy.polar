actor User {}

resource Organization {
  roles = ["admin"];
}

resource Team {
  roles = ["editor"];
}

resource Document {
  relations = { organization: Organization, team: Team };
  permissions = ["read", "write"];
  "read" if "admin" on "organization";
  "read" if has_status(resource, "published");
  "read" if is_public(resource);
  "write" if "editor" on "team";
}