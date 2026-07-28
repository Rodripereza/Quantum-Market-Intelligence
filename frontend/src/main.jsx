import React from "react";
import { createRoot } from "react-dom/client";

import "./styles/design-system/tokens.css";
import "./styles/design-system/reset.css";
import "./styles/design-system/typography.css";
import "./styles/design-system/layout.css";
import "./styles/design-system/components.css";
import "./styles/design-system/utilities.css";

import "./style.css";
import "./styles/pages/overview.css";

import App from "./App";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);