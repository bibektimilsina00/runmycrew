// fuse v2 — root app
const { useState: useAppState } = React;

function App() {
  const [screen, setScreen] = useAppState("gallery");
  const [project, setProject] = useAppState(null);

  return screen === "gallery" ? (
    <Gallery onOpenProject={(p) => { setProject(p); setScreen("canvas"); }} />
  ) : (
    <Canvas project={project} onBack={() => setScreen("gallery")} />
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
