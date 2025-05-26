import { useCallback, useEffect, useRef, useState } from "react";
import { HotTable } from "@handsontable/react-wrapper";
import { registerAllModules } from "handsontable/registry";

registerAllModules();

export default function PreviewPage() {
  const inputRef = useRef(null);
  const [data, setData] = useState();
  const [mapping, setMapping] = useState();
  const [xmlContent, setXmlContent] = useState();

  const [csv, setCSV] = useState("");

  const direct = ["key", "type", "summary", "created", "reporter", "parent"];
  const custom = [
    "Année-mois",
    "Axe ministériel",
    "Centre de coût",
    "Centre de coût(complet)",
    "Centre financier",
    "Date EJ/SF",
    "Domaine fonctionnel",
    "Département-Bureau",
    "Etat ConsoPrevu",
    "Ligne budgétaire",
    "Montant EJ/SF TTC",
  ];

  const gristSafeNames = [...direct, ...custom].map((n) => {
    return n
      .replace(/[ \-\/]/g, "_")
      .replace(/é/g, "e")
      .replace(/û/g, "u");
  });

  const config = {
    requiredAccess: "full",
    columns: gristSafeNames.map((name) => {
      if (name == "created" || name.startsWith("Date")) {
        return {
          name,
          type: "DateTime",
        };
      }
      return {
        name,
      };
    }),
  };

  useEffect(() => {
    window.grist.ready(config);

    window.grist.onOptions((options, settings) => {
      console.log({ options, settings });
    });
    window.grist.onRecord((record, mapping) => {
      setMapping(mapping);
    });
  }, []);

  useEffect(() => {
    if (!xmlContent) {
      return;
    }

    let done = true;
    const list = xmlContent.children[0].children[0].children;
    const data = [];
    for (var i in list) {
      const element = list[i];
      if (element.tagName !== "item") {
        continue;
      }

      const directData = direct.map((field) => {
        const f = element.getElementsByTagName(field)[0];
        return f?.innerHTML;
      });

      const customData = [...custom];
      const cfs = element.getElementsByTagName("customfields")[0];
      const customs = cfs.getElementsByTagName("customfield");
      for (const cf of customs) {
        const cfn = cf.getElementsByTagName("customfieldname")[0];
        const idx = custom.indexOf(cfn.textContent);
        if (idx >= 0) {
          const cfv = cf
            .getElementsByTagName("customfieldvalues")[0]
            .getElementsByTagName("customfieldvalue")[0]; //.innerHTML
          customData[idx] = cfv?.textContent;
        }
      }
      data.push([...directData, ...customData]);
    }

    setData(
      data.map((row) => {
        const k = row[0];

        const fields = row.reduce((a, v, i) => {
          const ff = mapping[gristSafeNames[i]];

          if (ff == "created" || ff.startsWith("Date")) {
            a[ff] = new Date(v).toISOString();
          } else {
            a[ff] = v;
          }
          return a;
        }, {});
        return {
          fields,
          require: {
            [mapping.key]: k,
          },
        };
      }),
    );
  }, [xmlContent]);

  async function updateXML(e) {
    const f = e.target.files[0];
    const textDecoder = new TextDecoder("utf-8"); // You can specify the encoding here
    const buffer = await f.arrayBuffer();
    const data = textDecoder.decode(buffer);
    const p = new DOMParser();
    const xml = p.parseFromString(data, "application/xml");
    setXmlContent(xml);
  }

  async function upload() {
    try {
      const tokenInfo = await window.grist.docApi.getAccessToken({
        readOnly: false,
      });
      const src = `${tokenInfo.baseUrl}/attachments?auth=${tokenInfo.token}`;
      let formData = new FormData();
      formData.append("upload", inputRef.current.files[0]);

      const re = await fetch(src, {
        method: "POST",
        body: formData,
      });
      const res = await re.json();
      console.log(res);
    } catch (e) {
      console.log(e);
    }
  }

  async function download() {
    try {
      const tokenInfo = await window.grist.docApi.getAccessToken({
        readOnly: false,
      });
      const id = 136;
      const src = `${tokenInfo.baseUrl}/attachments/${id}/download?auth=${tokenInfo.token}`;
      const re = await fetch(src);
      const res = await re.text();
      console.log(res);
    } catch (e) {
      console.log(e);
    }
  }

  async function update() {
    const table = window.grist.getTable();
    const result = await table.upsert(data);
    inputRef.current.value = "";
    setData();
  }

  return (
    <>
      <div>
        {mapping ? (
          <>
            <p>Déposez un fichier XML de Chordée</p>
            <input
              ref={inputRef}
              type="file"
              onChange={updateXML}
              accept="application/xml"
            />
            <button disabled={!data?.length} onClick={update}>
              Mettre à jour {data?.length || "des"} éléments
            </button>
            {/*<button onClick={upload}>upload</button>
          <button onClick={download}>download</button>*/}
          </>
        ) : (
          <></>
        )}
      </div>
    </>
  );
}
