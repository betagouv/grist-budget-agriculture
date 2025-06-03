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

  async function requestResult(format, record) {
    setDoing(true)
    const tokenInfo = await grist.docApi.getAccessToken({ readOnly: false });
    const data = {
      mapping,
      tokenInfo,
      format,
      record
    }

    const url = `/api/chorus/inf-bud-53${record ? "": "/aggregate"}`
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify(data),
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (response.status == 500) {
      alert('error')
    } else {
      var link = document.createElement("a");
      link.download = `inf_bud_53_${record ? `id_${record.id}` : 'agg'}.${format}`;
      link.href = URL.createObjectURL(await response.blob());
      link.click();
    }
    setDoing(false)
  }

  async function onClick(format) {
    await requestResult(format, record)
  }

  async function onAggregateClick(format) {
    await requestResult(format)
  }

  return (
    <div>
      <h1>GO CHORUS</h1>
      <button disabled={doing || !record} onClick={() => onClick("xlsx", record)}>Récupérer l'extraction Chorus filtrée pour les BC de la Ruche</button>
      {!record ? <p>Il faut sélectionner une ligne d'INF_BUG_53.</p> : ""}
      {process.env.NODE_ENV == "development" ? (
          <div>
            <button disabled={doing || !record} onClick={() => onClick("pickle", record)}>Récupérer l'extraction Chorus filtrée pour les BC de la Ruche (PICKLE)</button>
          </div>
        ) : (
          <></>
        )}
      <button disabled={doing} onClick={() => onAggregateClick("xlsx")}>Récupérer un état global en regroupant les extractions Chorus les plus récentes pour chaque année</button>
    </div>
  );
}
