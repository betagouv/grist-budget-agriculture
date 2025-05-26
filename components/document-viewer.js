import { useEffect, useState } from "react";

import PageCanvas from "./page-canvas.js";

function DocumentViewer(props) {
  const [pageCount, setPageCount] = useState();
  useEffect(() => {
    if (!props.document) {
      setPageCount();
    }

    setPageCount(props.document.numPages);
  }, [props.document]);

  function onClick({ pageNumber, e }) {
    props?.onClick({ pageNumber, x: e.x, y: e.y });
  }
  function onMouseMove({ pageNumber, e }) {
    props?.onMouseMove({ pageNumber, x: e.x, y: e.y });
  }

  return (
    <div>
      {[...Array(pageCount).keys()].map((pageNumber) => (
        <PageCanvas
          key={pageNumber}
          document={props.document}
          additions={props.additions?.filter((a) => a.pageNumber == pageNumber)}
          config={props.config}
          pageNumber={pageNumber}
          onClick={(e) => onClick({ pageNumber, e })}
          onMouseMove={(e) => onMouseMove({ pageNumber, e })}
          onMouseOut={() => props?.onMouseOut?.()}
        />
      ))}
    </div>
  );
}

export default DocumentViewer;
