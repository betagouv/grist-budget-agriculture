import { useState, useEffect, useRef } from "react";

export default function DuplicatePage() {
  const [previsionnel, setPrevisionnel] = useState();
  const [wip, setWIP] = useState(false);

  useEffect(() => {
    window.grist.ready({
      requiredAccess: "full",
    });
    window.grist.onRecord((record) => {
      setPrevisionnel(record);
    });
    window.grist.onNewRecord(() => {
      setPrevisionnel();
    });
  }, []);
  function actionTitle() {
    return `Dupliquer le prévisionnel du ${previsionnel.Date.toLocaleDateString()} pour ${previsionnel.Produit}`;
  }

  async function duplicate() {
    setWIP(true);
    const table = window.grist.getTable();
    const result = await table.create({
      fields: {
        Produit: previsionnel.Produit_.rowId,
        CP_2025_d_AE_d_annees_precedentes:
          previsionnel.CP_2025_d_AE_d_annees_precedentes,
        Date: new Date(),
        Libelle: "Nouveau prévisionnel",
      },
    });
    const depenses = await window.grist.docApi.fetchTable(
      "Depenses_previsionnelles",
    );
    const toCreate = depenses.Previsionnel.map((v, i) => {
      if (v !== previsionnel.id) {
        return;
      } else {
        return {
          fields: {
            Intitule: depenses.Intitule[i],
            Montant_AE: depenses.Montant_AE[i],
            CP_2025: depenses.CP_2025[i],
            Previsionnel: result.id,
          },
        };
      }
    }).filter((v) => v);
    window.grist.setSelectedRows([result.id]);
    window.grist.setCursorPos({ rowId: result.id });
    const additions = await window.grist
      .getTable("Depenses_previsionnelles")
      .create(toCreate);
    setWIP(false);
  }

  return (
    <div className="fullPage">
      {previsionnel ? (
        <button disabled={wip} onClick={duplicate}>
          {actionTitle()}
        </button>
      ) : (
        <div>Un prévisionnel doit être sélectionné.</div>
      )}
    </div>
  );
}
