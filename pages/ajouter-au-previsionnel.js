import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import jsonwebtoken from "jsonwebtoken";

import { filterMonthRowRecords } from "../lib/month.mjs";

export default function InspectOnRecords() {
  const searchParams = useSearchParams();
  const period = searchParams.get("period");
  const [record, setRecord] = useState();
  const [allMonths, setAllMonths] = useState();
  const [month, setMonth] = useState();

  useEffect(() => {
    window.grist.ready({
      requiredAccess: "full",
    });
    window.grist.onRecord(async (record) => {
    	setRecord(record);
    });

    async function getMonths() {
      const recordData = await window.grist.docApi.fetchTable("Mois_de_facturation")
      setAllMonths(recordData);
    }
    getMonths()
  }, []);

  useEffect(() => {
    if (!period || !allMonths) {
      return
    }
    const months = filterMonthRowRecords(allMonths, period)
    setMonth(months[0])
  }, [period, allMonths])

  function addRow() {
    window.grist.getTable("Conso_mensuelle").create([{fields: {
      Contrat_Freelance: record.id,
      Nb_jours_factures: 0,
      Mois: month.id
    }}])
  }
  function show(month) {
    if (!month) {
      return
    }
    const d = new Date(month.c1er_du_mois*1000)
    return d.toLocaleDateString(undefined, { month: "long", year: "numeric"})
  }

  return (
    <div className="fullPage">
      { record ? (
        record.Conso >= 1 ? <div><i>Le contrat freelance apparait déjà dans le prévisionnel.</i></div> :
            <button onClick={addRow}>Ajouter une ligne au prévisionnel pour ce contrat freelance<br/>
              <i>En ajoutant une conso mensuelle prévisionnelle<br/>avec zéro jour sur le mois de {show(month)}</i></button>
        ) : <div>Un contrat freelance doit être sélectionné.</div>
      }
    </div>
  );
}
