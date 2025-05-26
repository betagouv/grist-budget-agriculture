/** @type {import('next').NextConfig} */

const isProduction = "production" === process.env.NODE_ENV;

const nextConfig = {
  basePath: isProduction ? "/grist-previsionnel" : "",
  output: "export",
  reactStrictMode: true,
};

export default nextConfig;
