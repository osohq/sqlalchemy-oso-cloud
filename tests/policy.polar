actor User {}

resource Organization {
  roles = ["admin"];
}

resource Document {
  relations = { organization: Organization };
  permissions = ["read"];
  "read" if "admin" on "organization";
}