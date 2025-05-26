import { useEffect, useState } from "react";
import additionTypes from "../lib/addition-types.js";

function AdditionBlock({
  selectedAdditionType,
  setSelectedAdditionType,
  setShowEdit,
  additions,
  config,
  onRemoveAddition,
  children,
}) {
  const [additionOptions, setAdditionOptions] = useState([]);
  useEffect(() => {
    setAdditionOptions([
      { name: "None", enabled: true },
      ...Object.keys(additionTypes).map((additionType) => {
        const enabled = additionTypes[additionType].enabled(config);
        return {
          value: additionType,
          name: additionTypes[additionType].name,
          enabled,
        };
      }),
    ]);
  }, [config]);

  return (
    <div className="addition-block">
      <fieldset>
        <legend>Addition</legend>
        {additionOptions.map((o) => (
          <div key={o.value || o.name}>
            <label className={!o.enabled ? "disabled" : ""}>
              <input
                type="radio"
                name="addition"
                value={o.value}
                onChange={() => setSelectedAdditionType(o.value)}
                checked={selectedAdditionType == o.value}
                disabled={!o.enabled}
              />
              {o.name}
            </label>
          </div>
        ))}
        <button onClick={() => setShowEdit(true)}>Edit config</button>
      </fieldset>
      {additions.length ? (
        <fieldset>
          <legend>Additions</legend>
          {additions.map((a, i) => (
            <div key={[a.type, a.x, a.y, a.pageNumber].join("-")}>
              <button onClick={() => onRemoveAddition(i)}>
                Remove {a.type} page {a.pageNumber + 1}
              </button>
            </div>
          ))}
        </fieldset>
      ) : (
        <></>
      )}
      <div>{children}</div>
    </div>
  );
}

export default AdditionBlock;
