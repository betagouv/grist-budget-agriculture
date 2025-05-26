"use client";
import { useCallback, useEffect, useRef, useState, StrictMode } from "react";
import { useSearchParams } from "next/navigation";

export default function MessagePage() {
  const searchParams = useSearchParams();
  const origin = searchParams.get("from");
  const [record, setRecord] = useState();
  const [people, setPeople] = useState([]);
  const [peopleText, setPeopleText] = useState("");
  const [newInChargeIndexes, setNewInChargeIndexes] = useState([]);
  const [comment, setComment] = useState("");

  const [done, setDone] = useState(false);
  useEffect(() => {
    window.grist.ready({
      requiredAccess: "full",
    });

    window.grist.docApi.fetchTable("Personnes").then((data) => {
      setPeople(data);
    });

    window.grist.onRecord(async (record, mapping) => {
      setRecord(record);
    });
  }, []);

  async function add() {
    const data = newInChargeIndexes.map((idx) => people.id[idx]);
    await window.grist.getTable().update([
      {
        id: record.id,
        fields: {
          Personnes_en_charge: ["L", ...data],
        },
      },
    ]);
    setComment("");
    setNewInChargeIndexes([]);
    setDone(true);

    if (!newInChargeIndexes.length) {
      return;
    }

    const notifs = window.grist.getTable("Notifications");
    await notifs.create({
      fields: {
        [origin]: record.id,
        Commentaires: comment,
      },
    });
  }

  function onPeopleTextChange(e) {
    const text = e.target.value;
    if (!text.startsWith("#")) {
      setPeopleText(text);
      return;
    }

    setNewInChargeIndexes([...newInChargeIndexes, parseInt(text.slice(1))]);
    setPeopleText("");
  }

  function removeIndex(indexToDrop) {
    setNewInChargeIndexes([
      ...newInChargeIndexes.filter((a, i) => i != indexToDrop),
    ]);
  }

  return done ? (
    <div>
      <div>Bien reçu</div>
      <div></div>
      <button onClick={() => setDone(false)}>
        Réattribuer un autre {origin?.replace?.(/_/g, " ")?.toLowerCase()}
      </button>
    </div>
  ) : (
    <>
      <div>
        {origin?.replace?.(/_/g, " ")} #{record?.id}
      </div>
      <div>
        <label for="in-charge">Prochaines personnes en charge</label>
        <div>
          <input
            id="in-charge"
            list="Nom_d_usage"
            onChange={onPeopleTextChange}
            value={peopleText}
          />
          <datalist id="Nom_d_usage">
            {people &&
              people.Nom_d_usage?.map((n, i) => (
                <option key={people.id[i]} value={`#${i}`} label={n} />
              ))}
          </datalist>
        </div>
      </div>
      <ul>
        {newInChargeIndexes.map((dataIdx, idx) => (
          <li key={dataIdx}>
            {people.Nom_d_usage[dataIdx]}
            <button onClick={() => removeIndex(idx)}>Supprimer</button>
          </li>
        ))}
      </ul>
      <label for="comment">Commentaires</label>
      <div>
        <textarea
          id="comment"
          cols={40}
          rows={10}
          onChange={(e) => setComment(e.target.value)}
          value={comment}
        />
      </div>
      <div>
        <button onClick={add} disabled={newInChargeIndexes.length == 0}>
          Mettre à jour & notifier par email
        </button>
      </div>
      <div>
        <button onClick={add} disabled={newInChargeIndexes.length != 0}>
          Enlever toutes les personnes en charge
        </button>
      </div>
    </>
  );
}
