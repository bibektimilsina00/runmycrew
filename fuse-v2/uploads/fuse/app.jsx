// fuse — root app
const { useState: useState_ } = React;

function App() {
  const [screen, setScreen] = useState_("gallery");
  const [project, setProject] = useState_(null);

  return screen === "gallery" ? (
    <Gallery onOpenProject={(p) => { setProject(p); setScreen("canvas"); }} />
  ) : (
    <Canvas project={project} onBack={() => setScreen("gallery")} />
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
