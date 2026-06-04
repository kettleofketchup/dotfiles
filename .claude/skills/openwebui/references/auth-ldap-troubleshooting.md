# LDAP Authentication Troubleshooting

## `port must be an integer`

**Cause:** `LDAP_SERVER_PORT` is being passed as a string with quotes.

**Solution:** Remove quotes from the port value (`LDAP_SERVER_PORT=389`) and remove protocol prefixes from `LDAP_SERVER_HOST`.

## `[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred`

**Cause:** TLS handshake failure.

**Solution:**
- No TLS: Set `LDAP_USE_TLS="false"`, connect to port `389`
- LDAPS: Configure server for TLS on port `636`, set `LDAP_USE_TLS="true"`
- StartTLS: Connect on port `389`, set `LDAP_USE_TLS="true"`

## `err=49 text=` (Invalid Credentials)

**Cause:** Incorrect DN or password for bind attempt.

**Solution:**
1. Verify the password matches the `userPassword` in the LDIF
2. Check the User DN is correct (`uid=jdoe,ou=users,dc=example,dc=org`)
3. Test with `ldapwhoami`:
   ```bash
   ldapwhoami -x -H ldap://localhost:389 \
     -D "uid=jdoe,ou=users,dc=example,dc=org" -w "password123"
   ```
4. Reset password if needed using `ldapmodify` or `ldappasswd`

### Change Password via LDIF

```ldif
dn: uid=jdoe,ou=users,dc=example,dc=org
changetype: modify
replace: userPassword
userPassword: {PLAIN}newpassword
```

Apply with:

```bash
docker exec openldap ldapmodify -x -D "cn=admin,dc=example,dc=org" \
  -w admin -f /path/to/change_password.ldif
```
