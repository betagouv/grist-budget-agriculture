import { useState, useEffect, useRef } from "react";

const name = "Name";
const amountAE = "AE";
const amountCP = "CP";
const year = "Year";
const product = "Product";

export default function FinancementsVersPrevisionnelPage() {
  const [depenses, setDepenses] = useState([]);
  const [mapping, setMapping] = useState();

  useEffect(() => {
    window.grist.ready({
      requiredAccess: "full",
      columns: [
        {
          name: name,
          type: "Text",
        },
        {
          name: amountAE,
          type: "Numeric",
        },
        {
          name: amountCP,
          type: "Numeric",
        },
        {
          name: year,
        },
        {
          name: product,
        },
      ],
    });
    window.grist.onRecords((records, mapping) => {
      setDepenses(records);
      setMapping(mapping);
    });
  }, []);

  async function createPrevisionnel() {
    const table = window.grist.getTable("Previsionnels");
    const result = await table.create({
      fields: {
        Produit: depenses[0][mapping[product]].rowId,
        Date: new Date(),
        Libelle: "Nouveau prévisionnel",
      },
    });

    const depensesTable = await window.grist.getTable(
      "Depenses_previsionnelles",
    );
    const toSave = depenses.filter((d) => d[mapping[year]] === "2025");
    const data = toSave.map((item) => {
      return {
        fields: {
          Intitule: item[mapping[name]],
          Montant_AE: item[mapping[amountAE]],
          CP_2025: item[mapping[amountCP]],
          Previsionnel: result.id,
        },
      };
    });
    await depensesTable.create(data);
  }

  return (
    <div className="fullPage">
      <button onClick={createPrevisionnel}>
        Enregistrer les financements 2025 comme un prévisionnel
      </button>
    </div>
  );
}
