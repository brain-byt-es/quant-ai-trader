import type { NextConfig } from "next";
import path from "path";
import dotenv from "dotenv";

// Load environment variables from the root .env file
dotenv.config({ 
  path: path.resolve(__dirname, "../.env"),
  quiet: true 
});

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  
  // Proxy /api/py to the FastAPI backend
  async rewrites() {
    return [
      {
        source: "/api/py/:path*",
        destination: process.env.NODE_ENV === "development" 
          ? "http://127.0.0.1:8000/:path*" 
          : "http://127.0.0.1:8000/:path*", // Update this for production URL if needed
      },
    ];
  },
};

export default nextConfig;
