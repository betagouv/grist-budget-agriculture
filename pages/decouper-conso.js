import { useCallback, useEffect, useRef, useState } from "react";
import { HotTable } from "@handsontable/react-wrapper";
import { registerAllModules } from "handsontable/registry";
import equal from "fast-deep-equal";

registerAllModules();

function algo(extra, total, jours, frais) {
  if (extra <= frais) {
    return [
      [jours, frais - extra, total - extra],
      [0, extra, extra],
    ];
  }
  const hors_frais = total - frais;
  if (extra <= hors_frais) {
    const par_jour = hors_frais / jours;
    const extra_jour = extra / par_jour;
    return [
      [jours - extra_jour, frais, total - extra],
      [extra_jour, 0, extra],
    ];
  }

  const offset = total - extra;
  return [
    [0, offset, offset],
    [jours, frais - offset, total - offset],
  ];
}

const tests = [
  {
    input: { extra: 100, total: 1200, jours: 10, frais: 200 },
    output: [
      [10, 100, 1100],
      [0, 100, 100],
    ],
  },
  {
    input: { extra: 300, total: 1200, jours: 10, frais: 200 },
    output: [
      [7, 200, 900],
      [3, 0, 300],
    ],
  },
  {
    input: { extra: 1100, total: 1200, jours: 10, frais: 200 },
    output: [
      [0, 100, 100],
      [10, 100, 1100],
    ],
  },
];

export default function DecouperConsoPage() {
  const [conso, setConso] = useState();
  const [message, setMessage] = useState("Récupération en cours.");
  const [input, setInput] = useState();
  const [suggestion, setSuggestion] = useState();

  useEffect(() => {
    window.grist.ready({
      allowSelectBy: true,
      requiredAccess: "full",
    });
    window.grist.onRecord((record) => {
      setConso(record);
      if (record.BC_Reste_a_consommer === null) {
        setMessage("Aucun bon de commande sélectionné.");
      } else if (Math.abs(record.BC_Reste_a_consommer) < 0.005) {
        setMessage("Le bon de commande est déjà entièrement consommé.");
      } else if (record.BC_Reste_a_consommer > 0) {
        setMessage(
          "Le bon de commande n'est pas sur-consommé, il n'est donc pas nécessaire découper la conso en deux.",
        );
      } else if (record.Total_Facture_TTC < -record.BC_Reste_a_consommer) {
        setMessage(
          "La conso. mensuelle sélectionnée ne peux pas être découpée en deux pour solder le bon de commande.",
        );
      } else {
        const results = tests
          .map((t, i) => {
            const input = t.input;
            const res = algo(
              input.extra,
              input.total,
              input.jours,
              input.frais,
            );
            const ok = equal(t.output, res);
            if (!ok) {
              return `test ${i}`;
            }
          })
          .filter((v) => v !== undefined);
        if (results.length) {
          setMessage(results.join(",") + " en erreur.");
        } else {
          setMessage();
        }
      }
      const extra = -record.BC_Reste_a_consommer;
      const total = record.Total_Facture_TTC;
      const jours = record.Nb_jours_factures;
      const frais = record.Autres_frais_TTC;
      setInput([[jours, frais, total]]);
      setSuggestion(algo(extra, total, jours, frais));
    });
  }, []);

  const colHeaders = [
    "Nb_jours_factures",
    "Autres_frais_TTC",
    "Total_Facture_TTC",
  ];

  async function split() {
    const newRecord = await window.grist.selectedTable.create({
      fields: {
        Contrat_Freelance: conso.Contrat_Freelance.rowId,
        Mois: conso.Mois2.rowId,
        Statut: conso.Statut,
        Nb_jours_factures: suggestion[1][0],
        Autres_frais_TTC: suggestion[1][1],
      },
    });

    const existingRecord = await window.grist.selectedTable.update({
      id: conso.id,
      fields: {
        Nb_jours_factures: suggestion[0][0],
        Autres_frais_TTC: suggestion[0][1],
      },
    });
    grist.setCursorPos({ rowId: newRecord.rowId });
  }

  return (
    <>
      {message ? (
        <>{message}</>
      ) : (
        <>
          <div>
            <p>
              Séparer la conso. mensuelle sélectionée de {conso?.Personne} pour
              le mois de {conso?.Mois} :
            </p>
            <HotTable
              height="auto"
              colHeaders={colHeaders}
              type={"numeric"}
              data={input}
              readOnly={true}
              className="htRight"
              licenseKey="non-commercial-and-evaluation"
            />
            <p>en</p>
            <HotTable
              height="auto"
              colHeaders={colHeaders}
              type={"numeric"}
              className="htRight"
              readOnly={true}
              data={suggestion?.map((r) =>
                r.map((v) => Math.round(v * 100) / 100),
              )}
              licenseKey="non-commercial-and-evaluation"
            />
          </div>
          <button onClick={split}>Séparer la conso. mensuelle en deux</button>
        </>
      )}
    </>
  );
}
