import { useEffect, useState } from "react";
import jsonwebtoken from "jsonwebtoken";

export default function InspectOnRecords() {
  const [dump, setDump] = useState({});

  useEffect(() => {
    window.grist.ready({
      requiredAccess: "full",
    });
    window.grist.onRecords(async (records) => {
      const tokenInfo = await grist.docApi.getAccessToken({ readOnly: true });
      const tableId = await window.grist.getTable().getTableId();

      const url = `${tokenInfo.baseUrl}/tables/${tableId}/records?auth=${tokenInfo.token}`;
      const response = await fetch(url);
      setDump({
        response: await response.json(),
        token: jsonwebtoken.decode(tokenInfo.token),
      });
    });
  }, []);

  return (
    <div>
      <h1>TEST</h1>
      <pre>{JSON.stringify(dump, null, 2)}</pre>
    </div>
  );
}
