# Database Schema (PostgreSQL)

## Tables

### `products`
- `id` (UUID, PK)
- `name` (String)
- `base_url` (String)
- `category` (String)
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

### `pages`
- `id` (UUID, PK)
- `product_id` (UUID, FK)
- `url` (String)
- `title` (String)
- `is_authenticated` (Boolean)
- `created_at` (Timestamp)

### `modules`
- `id` (UUID, PK)
- `product_id` (UUID, FK)
- `name` (String)
- `description` (Text)

### `features`
- `id` (UUID, PK)
- `product_id` (UUID, FK)
- `module_id` (UUID, FK)
- `name` (String)
- `description` (Text)
- `evidence_url` (String)
- `evidence_text` (Text)
- `status` (Enum: IMPLEMENTED, PROPOSED)

### `personas`
- `id` (UUID, PK)
- `product_id` (UUID, FK)
- `name` (String)
- `description` (Text)

### `screenshots`
- `id` (UUID, PK)
- `feature_id` (UUID, FK)
- `type` (Enum: RAW, MARKETING)
- `image_url` (String)
- `created_at` (Timestamp)

### `generated_content`
- `id` (UUID, PK)
- `product_id` (UUID, FK)
- `type` (Enum: LINKEDIN_POST, LINKEDIN_PAGE, CAROUSEL, VIDEO_SCRIPT)
- `content` (Text)
- `status` (Enum: DRAFT, APPROVED, EXPORTED)
- `created_at` (Timestamp)
