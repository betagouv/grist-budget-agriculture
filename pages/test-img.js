import { useEffect, useRef, useState } from "react";

export default function SignPDFPage() {
  const ref = useRef(null);

  function set(input) {
    const b = input.target.files[0];

    const reader = new FileReader();
    reader.addEventListener(
      "load",
      () => {
        localStorage.setItem("signature", reader.result);
        const img = document.createElement("img");
        img.src = reader.result;
        ref.current.appendChild(img);
      },
      false,
    );
    reader.readAsDataURL(b);
  }

  function get() {
    const raw = localStorage.getItem("signature");
    const img = document.createElement("img");
    img.src = raw;
    ref.current.appendChild(img);
  }
  return (
    <div>
      <div>
        <input type="file" accept="image/*" onChange={set} />
      </div>
      <button onClick={set}>SET</button>
      <button onClick={get}>GET</button>
      <div ref={ref} />
    </div>
  );
}
