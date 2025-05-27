import { useEffect, useState } from "react";

const key = "Piece_jointe";

export default function InfBud53() {
  const [mapping, setMapping] = useState();
  const [record, setRecord] = useState();
  const [doing, setDoing] = useState(false);

  useEffect(() => {
    window.grist.ready({
      requiredAccess: "full",
      columns: [
        {
          name: key,
          type: "Attachments",
        },
      ],
    });

    window.grist.onRecord(async (record, mapping) => {
      setRecord(record)
      setMapping(mapping)
    });
  })

  async function onClick() {
    setDoing(true)
    const tokenInfo = await grist.docApi.getAccessToken({ readOnly: false });
    const data = {
      record,
      mapping,
      tokenInfo
    }

    const url = "/api/chorus/inf-bud-53"
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify(data),
      headers: {
        "Content-Type": "application/json",
      },
    });
    var link = document.createElement("a");
    link.download = `inf_bud_53_id_${record.id}.xlsx`;
    link.href = URL.createObjectURL(await response.blob());
    link.click();
    setDoing(false)
  }

  return (
    <div>
      <h1>GO CHORUS</h1>
      <button disabled={doing || !record} onClick={onClick}>Récupérer l'extraction Chorus filtrée pour les BC de la Ruche</button>
      {!record ? <p>Il faut sélectionner une ligne d'INF_BUG_53.</p> : ""}
    </div>
  );
}
