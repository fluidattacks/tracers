import React from "react";
import ReactDOM from "react-dom";

const root = document.getElementById("root");

if (root) {
  root.removeAttribute('id');

  ReactDOM.render(
    <React.StrictMode>
      Welcome!
    </React.StrictMode>,
    root,
  );
}
