**URL** : `/user/token/`

**Method** : `POST`

**Auth required** : YES

**Permissions required** : None

## Data Example
```json
{"email": "user@uw.edu",
 "password": "supersecret"}

```

## Success Response

**Code** : `201 OK`

**Content examples**

```json
{"token":"supersecrettoken"}
```

## Error Response

**Code** : `400 Bad Request`

**Content examples**

```json
{"non_field_errors":["Unable to authenticate with provided credentials"]}ß
```

## Notes

* Account must be created before reqeusting token
