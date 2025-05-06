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
  preview: {
    port: process.env.PORT || 10000,
    host: "0.0.0.0", // Listen on all network interfaces
    allowedHosts: [
      "papernexus.onrender.com",
      "papernexus-finder.onrender.com",
      ".onrender.com",
    ],
  },
});
