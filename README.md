# library-project

A project for the Pushkin Library

## Example of `config/config.json`

```JSON
{
  "debug": true,
  "allowed_hosts": [
    "127.0.0.1",
    "localhost"
  ],
  "secret_key": "super-secret-random-long-string-here",
  "db_backend": "sqlite3",
  "db_name": "config/db.sqlite3",
  "media_root": "media",
  "static_root": "static",
  "url_prefix": "",
  "server_email": "project@example.com",
  "email_use_tls": true,
  "email_use_ssl": false,
  "email_host": "mail.example.com",
  "email_port": 25,
  "email_host_user": "user",
  "email_host_password": "password",
  "admins": [
    ["admin", "admin@example.com"]
  ]
}
```
