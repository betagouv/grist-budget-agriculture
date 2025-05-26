import { useCallback, useEffect, useRef, useState } from "react";
import { HotTable } from "@handsontable/react-wrapper";
import { registerAllModules } from "handsontable/registry";

registerAllModules();

function filterMonthRowRecords(data) {
  const names = Object.keys(data);
  const years = data.Annualite_budgetaire;

  const filteredData = years.reduce((a, y, i) => {
    if (y == 2025) {
      a.push(
        names.reduce((res, n) => {
          res[n] = data[n][i];
          return res;
        }, {}),
      );
    }
    return a;
  }, []);

  return filteredData.toSorted((a, b) => a.c1er_du_mois - b.c1er_du_mois);
}

export default function PreviewPage() {
  const hotRef = useRef(null);
  const [months, setMonths] = useState([]);
  const [data, setData] = useState();
  const [rowData, setRowData] = useState([]);
  const [tableData, setTableData] = useState([]);
  const [log, setLog] = useState("");

  useEffect(() => {
    window.grist.ready({
      allowSelectBy: true,
      requiredAccess: "full",
    });
    window.grist.onRecords((records) => {
      setData(records);
    });
    async function fetchMonths() {
      const recordData = await window.grist.docApi.fetchTable(
        "Mois_de_facturation",
      );
      setMonths(filterMonthRowRecords(recordData));
    }
    fetchMonths();
  }, []);

  useEffect(() => {
    if (!data?.length) {
      setRowData([]);
      return;
    }
    const dataByNames = {};
    data.forEach((r) => {
      const personKey = [r.Personne, r.Domaine].join(" - ");
      dataByNames[personKey] = dataByNames[personKey] || {
        Personne: personKey,
        values: {},
      };
      dataByNames[personKey].values[r.Mois] =
        dataByNames[personKey].values[r.Mois] || [];
      dataByNames[personKey].values[r.Mois].push(r);
    });
    const names = Object.keys(dataByNames);
    names.sort();
    setRowData(names.map((n) => dataByNames[n]));
  }, [data]);

  const accSum = (a, v) => a + (v || 0);
  const amountDisplay = (v) =>
    v.toLocaleString("FR-fr", { style: "currency", currency: "EUR" });

  const buildTableData = useCallback(() => {
    const data = rowData.map((person) => {
      return [
        person.Personne,
        ...months.map((m, i) => {
          return person.values[m.Mois_de_facturation]
            ?.map((v) => v.Nb_jours_factures)
            .reduce(accSum, 0);
        }),
      ];
    });

    data.forEach((r, i) => {
      r.push("");
      const v = months
        .map((m) => {
          const person = rowData[i];
          return person.values[m.Mois_de_facturation]
            ?.map((v) => v.Total_Facture_TTC)
            .reduce(accSum, 0);
        })
        .reduce(accSum, 0);
      r.push(amountDisplay(v));
    });

    const sumData = months.map((m) => {
      const total = rowData
        .map((r) => {
          return r.values[m.Mois_de_facturation]
            ?.map((v) => v.Total_Facture_TTC)
            .reduce(accSum, 0);
        })
        .reduce(accSum, 0);
      return total;
    });
    const fullSum = sumData.reduce(accSum, 0);
    sumData.push("");
    sumData.push(fullSum);

    setTableData([...data, [], ["Total", ...sumData.map(amountDisplay)]]);
  }, [rowData, months]);

  useEffect(() => {
    buildTableData();
  }, [months, rowData]);

  const getCellData = useCallback(
    (row, column) => {
      const details = rowData[row];
      return details?.values?.[months[column - 1]?.Mois_de_facturation];
    },
    [rowData, months],
  );

  function afterSelectionEnd(row, column) {
    if (row < 0) {
      return;
    }
    const input = getCellData(row, column);
    const rowId = input?.length === 1 ? input[0].id : "new";
    grist.setCursorPos({ rowId });
  }

  function afterChange(changes, source) {
    if (
      source !== "edit" &&
      source !== "Autofill.fill" &&
      !source.startsWith("UndoRedo.")
    ) {
      console.info(`Ignore change from ${source}`);
      if (source !== "updateData" && source !== "ColumnSummary.reset") {
        buildTableData();
      }
      return;
    }

    const updatesOrAdditions = changes
      .filter(([row, prop, oldValue, newValue]) => {
        return oldValue != newValue;
      })
      .map((change) => {
        const row = change[0];
        const column = change[1];
        const month = months[column - 1];
        const newValue = change[3] || 0;

        const rowDetails = rowData[row];
        const rowId = rowDetails.values[month.Mois_de_facturation]?.[0]?.id;
        if (rowId) {
          return {
            require: { id: rowId },
            fields: {
              Nb_jours_factures: newValue,
            },
          };
        }
        const mm = Object.keys(rowDetails.values);
        const firstConso = rowDetails.values[mm[0]][0];
        const p = firstConso.ProchainContrat.rowIds[0];
        const m = months[column - 1].id;
        return {
          fields: {
            Contrat_Freelance: p,
            Mois: m,
            Nb_jours_factures: newValue,
            Statut: "Estimation",
          },
          require: {
            Contrat_Freelance: p,
            Mois: m,
          },
        };
      });

    if (updatesOrAdditions.length == 0) {
      buildTableData();
      return;
    }

    const table = window.grist.getTable();
    table
      .upsert(updatesOrAdditions)
      .then((r) => {
        console.log(r);
      })
      .catch((e) => {
        console.error(e);
      })
      .finally((f) => {
        console.log("f", f);
      });
  }

  return (
    <>
      <HotTable
        ref={hotRef}
        data={tableData}
        rowHeaders={false}
        colHeaders={[
          "Personne",
          ...(months.map((m) => m.Mois_de_facturation) || []),
          "",
          "Total",
        ]}
        columns={[
          {
            type: "text",
            readOnly: true,
          },
          ...[...months, ...["", "Total"]].map(() => {
            return {
              type: "numeric",
              className: "htRight",
            };
          }),
        ]}
        height="auto"
        licenseKey="non-commercial-and-evaluation"
        afterSelectionEnd={afterSelectionEnd}
        afterChange={afterChange}
        copyPaste={true}
        cells={(row, column) => {
          const cellProperties = {};
          if (row >= rowData.length || column > 12) {
            cellProperties.readOnly = true;
          } else if (column > 0) {
            const input = getCellData(row, column);
            if (input) {
              const classNames = [];
              if (input.length > 1) {
                classNames.push("italic");
                cellProperties.readOnly = true;
              }
              if (
                input.filter((c) => c.Statut === "Réalisé").length ===
                input.length
              ) {
                classNames.push("bold");
                cellProperties.readOnly = true;
              }
              cellProperties.className = classNames.join(" ");
            }
          }
          return cellProperties;
        }}
      />
      <div>
        <p>
          Les nombres de jours en <i>italique</i> sont calculés en sommant
          plusieurs consommations mensuelles. Pour cette raison, ils ne sont pas
          modifiables.
        </p>
        <p>
          Les nombres de jours en <b>gras</b> sont indiqués comme « Réalisé ».
          Pour cette raison, ils ne sont pas modifiables.
        </p>
      </div>
    </>
  );
}
