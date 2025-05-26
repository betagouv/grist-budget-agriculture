/** @type {import('next').NextConfig} */

const isProduction = "production" === process.env.NODE_ENV;
const dev = {
  rewrites: async () => {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:5328/api/:path*"
      },
    ];
  },
  output: "standalone"
};

const nextConfig = {
  output: "export",
  reactStrictMode: true,
  ...(isProduction ? {} : dev)
};

export default nextConfig;
