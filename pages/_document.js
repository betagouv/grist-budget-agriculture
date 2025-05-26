import { Html, Head, Main, NextScript } from "next/document";
import Script from "next/script";

export default function Document() {
  return (
    <Html lang="en">
      <Head />
      <body className={`env-${process.env.NODE_ENV}`}>
        {process.env.NODE_ENV == "development" ? (
          <div className="dev-warning">Environnement de DEV</div>
        ) : (
          <></>
        )}
        <Main className="main" />
        <NextScript />
        <Script
          src="https://grist.numerique.gouv.fr/grist-plugin-api.js"
          strategy="beforeInteractive"
          async=""
        />
      </body>
    </Html>
  );
}
