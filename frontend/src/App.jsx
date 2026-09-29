function App() {
  return (
    <div className="min-h-screen bg-bg-main flex items-center justify-center">
      <div className="bg-bg-sidebar border border-border rounded-lg p-8">
        <h1 className="text-text-header text-2xl font-bold mb-2">
          Real-Time Chat App
        </h1>
        <p className="text-text-secondary">
          Tailwind + Discord palette δοκιμή
        </p>
        <button className="mt-4 bg-accent hover:bg-accent-hover text-white px-4 py-2 rounded">
          Test κουμπί
        </button>
      </div>
    </div>
  )
}

export default App