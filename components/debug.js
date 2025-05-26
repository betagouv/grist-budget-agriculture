import { useCallback, useEffect, useRef, useState, StrictMode } from "react";

function Debug(props) {
  const [show, setShow] = useState(false);
  return (
    <div>
      <div>
        <label>
          <input
            type="checkbox"
            checked={show}
            onChange={() => setShow(!show)}
          />
          Show technical details
        </label>
      </div>
      {show ? <pre>{JSON.stringify(props.data, null, 2)}</pre> : <></>}
    </div>
  );
}

export default Debug;
