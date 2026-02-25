import { BrowserRouter, Route, Routes } from "react-router-dom";

import { useAnalysesState } from "./hooks/useAnalysesState";
import { InsightsPage } from "./pages/InsightsPage";
import { ReviewPage } from "./pages/ReviewPage";

export default function App() {
  const state = useAnalysesState();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ReviewPage {...state} />} />
        <Route path="/insights" element={<InsightsPage {...state} />} />
        <Route path="/insights/:id" element={<InsightsPage {...state} />} />
      </Routes>
    </BrowserRouter>
  );
}
