import { defineConfig } from "@neon/config/v1";

export default defineConfig({
  buckets: {
    screenshots: { access: "public_read" }
  },
});
