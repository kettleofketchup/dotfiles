# Administration Webhooks

Three types of webhook integrations are supported.

## 1. Admin Webhook: New User Notifications

Notifies administrators about new user sign-ups.

**Configuration:**
- **Admin Panel:** Navigate to **Admin Panel > Settings > General > Webhook URL**
- **Environment Variable:** Set `WEBHOOK_URL`

**Payload:**

```json
{
  "event": "new_user",
  "user": {
    "email": "tim@example.com",
    "name": "Tim"
  }
}
```

## 2. User Webhook: Chat Response Notifications

Notifies individual users when a model finishes generating a response. Only triggers when the user is not actively using the WebUI.

**Enabling:** Disabled by default. Enable via **Admin Panel > Settings > General > Features > User Webhooks** or set `ENABLE_USER_WEBHOOKS` environment variable.

**Configuration:** Users set their webhook URL in **Settings > Account > Notification Webhook**.

**Payload:**

```json
{
  "event": "chat_response",
  "chat": {
    "id": "abc-123-def-456",
    "title": "My Awesome Conversation",
    "last_message": "This is the prompt I submitted."
  }
}
```

## 3. Channel Webhooks: External Message Integration

Allow external services to post messages into Open WebUI channels.

**Use Cases:** System monitoring alerts, CI/CD notifications, custom automation (n8n, Zapier), external notification forwarding.

**Management:** Only channel managers and administrators can create/manage webhooks.

**Creating:**
1. Navigate to the channel
2. Click channel menu > **Edit Channel**
3. Open **Webhooks** section > **Manage** > **New Webhook**
4. Configure name and optional profile image
5. Copy the generated webhook URL

**Webhook URL Format:** `{WEBUI_API_BASE_URL}/channels/webhooks/{webhook_id}/{token}`

**Posting Messages:**

```bash
curl -X POST "https://your-instance.com/api/channels/webhooks/{webhook_id}/{token}" \
  -H "Content-Type: application/json" \
  -d '{"content": "Deployment completed successfully!"}'
```

**Response:**

```json
{
  "success": true,
  "message_id": "abc-123-def-456"
}
```

**Security:** Webhook URLs contain authentication tokens. Keep them secure. Anyone with the URL can post to the channel. Delete and recreate if compromised.

**Webhook Identity:** Messages appear with the webhook's name and profile image. User role is marked as "webhook". Deleted webhooks show "Deleted Webhook" as author.

## Troubleshooting

- Verify the webhook URL is correct
- Check external service webhook configuration
- Ensure firewall/proxy is not blocking outgoing requests
- Check Open WebUI server logs for error messages
