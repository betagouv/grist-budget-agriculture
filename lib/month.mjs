
function generateFilter(filterOptions) {
  if (!filterOptions) {
    return () => false
  }
  const parts = filterOptions.split(":")
  if (parts.length == 1) {
    const year = parseInt(parts[0])
    return (a, y, i, data) => {
      return y == year
    }
  }
  if (parts.length != 2) {
    throw "Oupsy"
  }
  const gte = parts[0]
  const lte = parts[1]
  return (a, y, i, data) => {
    const v = data.Mois_de_facturation[i]
    return (v >= gte) && (v < lte);
  }
}

export function filterMonthRowRecords(data, filter) {
  const names = Object.keys(data);
  const years = data.Annualite_budgetaire;

  const filterFct = generateFilter(filter);

  const filteredData = years.reduce((a, y, i) => {
    if (filterFct(a, y, i, data)) {
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
