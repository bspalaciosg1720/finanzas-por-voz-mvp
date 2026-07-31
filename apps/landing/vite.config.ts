import { cloudflare } from "@cloudflare/vite-plugin";
import { defineConfig } from "vite";
import vinext from "vinext";
import { cdnAdapter } from "@vinext/cloudflare/cache/cdn-adapter";

export default defineConfig({
  plugins: [
    vinext({
      cache: { cdn: cdnAdapter() },
    }),
    cloudflare({
      viteEnvironment: { name: "rsc", childEnvironments: ["ssr"] },
    }),
  ],
});
