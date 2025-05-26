import { useEffect, useRef, useState } from "react";

import * as pdfjsLibLatest from "pdfjs-dist";
import * as pdfjsLibLegacy from "pdfjs-dist/legacy/build/pdf.mjs";

import { Stage, Layer, Text, Image } from "react-konva";
import additionTypes from "../lib/addition-types.js";
import signatureScale from "../lib/signature-scale.js";

pdfjsLibLatest.GlobalWorkerOptions.workerSrc = "pdf.worker.mjs";
pdfjsLibLegacy.GlobalWorkerOptions.workerSrc = "pdf.worker.legacy.mjs";

function generateKey(a) {
  return [a.type, a.x, a.y, a.pageNumber].join(" ");
}
function PageCanvas(props) {
  const useLegacy = !!navigator.userAgent.match("Firefox/115");
  const pdfjsLib = useLegacy ? pdfjsLibLegacy : pdfjsLibLatest;
  pdfjsLib.GlobalWorkerOptions.workerSrc = useLegacy
    ? "pdf.worker.legacy.mjs"
    : "pdf.worker.mjs";

  const canvasRef = useRef(null);

  const [dims, setDims] = useState();
  const [additionShapes, setAdditionShapes] = useState([]);

  const paddingOffset = { x: 20, y: 20 };
  const checkShift = 0;

  useEffect(() => {
    if (!props.additions?.length) {
      setAdditionShapes([]);
    }
    const shapes = props.additions.map((a) => {
      if (a.type == "signature") {
        const raw = props.config.signature;
        const img = document.createElement("img");
        img.src = raw;
        const s = (
          <Image
            image={img}
            scale={{ x: 1 / signatureScale, y: 1 / signatureScale }}
            key={generateKey(a)}
            x={a.x + checkShift}
            y={a.y + checkShift}
          />
        );
        return s;
      } else {
        const meta = additionTypes[a.type];
        return (
          <Text
            key={generateKey(a)}
            x={a.x + checkShift}
            y={a.y + checkShift}
            fontFamily={"Times-Roman"}
            text={meta.text(props.config)}
            fontSize={15}
          />
        );
      }
    });
    setAdditionShapes(shapes);
  }, [props.additions, props.config]);

  function onPointerUp(e) {
    props?.onClick({
      x: e.evt.layerX, // - image.width() / 2,
      y: e.evt.layerY, // - image.height(),
    });
  }

  useEffect(() => {
    if (
      !canvasRef.current ||
      !props.document ||
      props.pageNumber === undefined
    ) {
      return;
    }
    async function render() {
      const page = await props.document.getPage(props.pageNumber + 1);
      var scale = 1;
      var viewport = page.getViewport({ scale: scale });

      var canvas = canvasRef.current;
      var canvasContext = canvas.getContext("2d");
      canvas.height = viewport.height;
      canvas.width = viewport.width;
      setDims({ height: viewport.height, width: viewport.width });

      var renderContext = {
        canvasContext,
        viewport,
      };
      var renderTask = page.render(renderContext);
      renderTask.promise.then(
        function () {},
        function () {},
      );
      return renderTask;
    }
    const promise = render();
    return () => {
      promise.then((task) => task.cancel());
    };
  }, [canvasRef, props.document, props.pageNumber]);

  return (
    <>
      <div className="page">
        <canvas className="page-background" ref={canvasRef}></canvas>
        {dims ? (
          <Stage
            className="konva-container"
            height={dims.height}
            width={dims.width}
            opacity={1}
            onPointerUp={onPointerUp}
          >
            <Layer>{additionShapes}</Layer>
          </Stage>
        ) : (
          <></>
        )}
      </div>
    </>
  );
}

export default PageCanvas;
