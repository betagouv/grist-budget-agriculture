
export function filterMonthRowRecords(data, year) {
  const names = Object.keys(data);
  const years = data.Annualite_budgetaire;

  const filteredData = years.reduce((a, y, i) => {
    if (y == year) {
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
