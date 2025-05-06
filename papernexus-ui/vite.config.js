import { defineConfig } from "vite";
import preact from "@preact/preset-vite";

export default defineConfig({
  plugins: [preact()],
  server: {
    proxy: {
      "/api": {
        target: "https://papernexus-finder.onrender.com",
        changeOrigin: true,
      },
    },
  },
});
