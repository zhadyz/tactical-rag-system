import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Development server configuration with dynamic port assignment
  server: {
    port: 5173,
    strictPort: false, // Allow auto-increment if port is busy
    watch: {
      // Ignore Tauri's Rust directory to prevent reload loops
      ignored: ["**/src-tauri/**"],
    },
  },

  // Build configuration optimized for Tauri
  build: {
    // Use modern ESNext target for better performance
    target: "esnext",
    // Minify in production, skip in debug mode for easier debugging
    minify: !process.env.TAURI_DEBUG ? "esbuild" : false,
    // Generate sourcemaps only in debug mode
    sourcemap: !!process.env.TAURI_DEBUG,
    // Output directory (Tauri expects "dist" by default)
    outDir: "dist",
  },

  // Prevent Vite from clearing the screen (plays better with Tauri CLI)
  clearScreen: false,

  // Environment variable prefix
  envPrefix: ["VITE_", "TAURI_"],
});
