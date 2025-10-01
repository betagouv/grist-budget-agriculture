import { useCallback, useEffect, useRef, useState } from "react";

const config = {
  requiredAccess: "full",
};


export default function PreviewPage() {
  useEffect(() => {
    window.grist.ready(config);

    window.grist.onOptions((options, settings) => {
      console.log({ options, settings });
    });
    window.grist.onRecord(() => {
    });
  }, []);

  async function onClickViaWidget() {
    await window.grist.getTable().create([{fields: { Type: "ViaWidget"}}])
  }

  async function onClickViaAccesToken() {
    const tokenInfo = await window.grist.docApi.getAccessToken({ readOnly: false });
    const tableId = "Table1"
    const url = `${tokenInfo.baseUrl}/tables/${tableId}/records?auth=${tokenInfo.token}`;
    const data = {records: [{fields: {Type: "ViaAccesToken"}}]}
    await fetch(url, {
      method: "POST",
      body: JSON.stringify(data),
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  return (
    <>
      <div>
        <h1>Démo</h1>
        <div><a href="https://github.com/gristlabs/grist-core/pull/1614">grist-core #1614</a></div>
        <div><button onClick={onClickViaWidget}>Add row via widget</button></div>
        <div><button onClick={onClickViaAccesToken}>Add row via access token</button></div>
      </div>
    </>
  );
}
