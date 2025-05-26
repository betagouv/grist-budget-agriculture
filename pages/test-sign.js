import { useEffect, useState } from "react";

import SignPDFComponent from "../components/sign.js";

export default function TestPage() {
  const [inputPDF, setInputPDF] = useState();

  useEffect(() => {
    async function get() {
      const contentUrl = `blank.pdf`;
      const response = await fetch(contentUrl);
      const buffer = await response.arrayBuffer();
      setInputPDF(buffer);
    }
    get();
  }, []);

  async function postNewT(event) {
    setInputPDF(await new Blob([event]).arrayBuffer());
  }

  async function postNew(event) {
    var link = document.createElement("a");
    link.download = "doc_signed.pdf";
    const b = new Blob([event]);
    link.href = URL.createObjectURL(b);
    link.click();
  }

  return <SignPDFComponent inputPDF={inputPDF} postNew={postNew} />;
}
