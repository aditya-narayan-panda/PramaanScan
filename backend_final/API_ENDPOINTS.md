# PramaanScan API endpoint inventory

Base URL: `/api/v1`

## Public
- `GET /health`
- `GET /verify/communication/{communication_id}`
- `POST /verify/file`
- `GET /communications/{communication_id}`
- `GET /communications/{communication_id}/versions`
- `GET /communications/{communication_id}/current`
- `GET /communications/{communication_id}/qr/image`
- `POST /media/analyze`

## Authentication
- `POST /auth/login`
- `POST /auth/admin/login`
- `POST /auth/institution/login`
- `POST /auth/refresh`
- `GET /auth/me`
- `POST /auth/logout`

## Authority/Admin
- `GET /dashboard/stats`
- `POST /communications/draft`
- `GET /communications`
- `PUT /communications/{communication_id}`
- `DELETE /communications/{communication_id}`
- `POST /communications/{communication_id}/versions/upload-register`
- `GET /communications/{communication_id}/qr`
- `GET /revocation/keys`
- `POST /revocation/key`
- `GET /revocation/key/{key_id}`
- `GET /verification/logs`
- `GET /verification/logs/{log_id}`
- `GET /analytics/overview`
- `GET /analytics/verifications`
- `GET /analytics/media`
- `GET /profile`
- `PUT /profile`
- `POST /profile/password`
- `GET /settings`
- `PUT /settings`

## Admin only
- `GET /admin/institutions`
- `POST /admin/institutions`
- `GET /admin/institutions/{institution_id}`
- `PUT /admin/institutions/{institution_id}`
- `DELETE /admin/institutions/{institution_id}`
- `GET /admin/users`
- `POST /admin/users`
- `GET /admin/users/{user_id}`
- `PUT /admin/users/{user_id}`
- `DELETE /admin/users/{user_id}`
- `GET /admin/audit-logs`

## Query controls

Documents, institutions, users and logs support pagination. Relevant endpoints support search/filter query parameters such as:

`page`, `page_size`, `search`, `status`, `media_type`, `category`, `role`, `issuer_id`, `result`, `source`.
