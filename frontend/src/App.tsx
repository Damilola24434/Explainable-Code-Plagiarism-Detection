// about the main app component
// this is the root react component that acts like a page router for this program.
// it uses browser History API to sync app state with browser navigation
// when user clicks a collection, it pushes state to history with collection id
// when user clicks back button, popstate event restores the previous state
// this way back/forward buttons work within the app instead of leaving it

import { useEffect, useState } from "react";
import Collections from "./Collections";
import CollectionDetails from "./CollectionDetails";
import Landing from "./Landing";

interface Collection {
  id: string;
  name: string;
  owner_id: string;
  created_at: string;
}

type NavItem = {
  label: string;
  onClick?: () => void;
  active?: boolean;
};

type AppState = {
  selectedCollection: Collection | null;
};

export default function App() {
  const [showLanding, setShowLanding] = useState(true);
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [navItems, setNavItems] = useState<NavItem[]>([{ label: "Collections", active: true }]);

  // Handle browser back/forward buttons
  useEffect(() => {
    const handlePopState = (event: PopStateEvent) => {
      const state = event.state as (AppState & { page?: string }) | null;
      
      if (state?.page === "landing") {
        setShowLanding(true);
      } else if (state?.selectedCollection) {
        setShowLanding(false);
        setSelectedCollection(state.selectedCollection);
        setNavItems([
          { label: "Collections", onClick: () => showCollections(), active: false },
          { label: state.selectedCollection.name, active: true },
        ]);
      } else {
        setShowLanding(false);
        setSelectedCollection(null);
        setNavItems([{ label: "Collections", active: true }]);
      }
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const showCollections = (e?: React.MouseEvent) => {
    e?.preventDefault();
    setSelectedCollection(null);
    setNavItems([{ label: "Collections", active: true }]);
    // Push history state for collections view
    window.history.pushState({ selectedCollection: null }, "", "/");
  };

  const handleGetStarted = () => {
    setShowLanding(false);
    window.history.pushState({ page: "collections" }, "", "/app");
  };

  const handleBackToLanding = () => {
    setShowLanding(true);
    setSelectedCollection(null);
    setNavItems([{ label: "Collections", active: true }]);
    window.history.pushState({ page: "landing" }, "", "/");
  };

  const handleSelectCollection = (collection: Collection) => {
    setSelectedCollection(collection);
    setNavItems([
      { label: "Collections", onClick: showCollections, active: false },
      { label: collection.name, active: true },
    ]);
    // Push history state for collection detail view
    window.history.pushState({ selectedCollection: collection }, "", `/collection/${collection.id}`);
  };

  const handleBackFromDetails = () => {
    setSelectedCollection(null);
    setNavItems([{ label: "Collections", active: true }]);
    // Use browser back instead of manual state change
    window.history.back();
  };

  return showLanding ? (
    <Landing onGetStarted={handleGetStarted} />
  ) : (
    <div className="app app-shell">
      <header className="site-nav navbar">
        <div className="site-nav-inner">
          <div className="nav-left">
            <button type="button" className="site-title brand-link" onClick={showCollections}>
              Plagiarism Detector
            </button>
            <button 
              type="button" 
              className="back-to-landing-btn"
              onClick={handleBackToLanding}
              title="Back to Home"
            >
              ← Home
            </button>
          </div>

          <nav className="nav-center" aria-label="Page navigation">
            {navItems.map((item, index) => (
              <span key={`${item.label}-${index}`} className="crumb-group">
                {item.onClick ? (
                  <button
                    type="button"
                    className={`nav-link crumb-link${item.active ? " active" : ""}`}
                    onClick={item.onClick}
                  >
                    {item.label}
                  </button>
                ) : (
                  <span className={`nav-link crumb-link${item.active ? " active" : ""}`}>
                    {item.label}
                  </span>
                )}
              </span>
            ))}
          </nav>

          <div className="nav-right">
            <input
              type="search"
              className="nav-search"
              placeholder={selectedCollection ? "Search datasets" : "Search collections"}
              aria-label={selectedCollection ? "Search datasets" : "Search collections"}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </header>
      <main className="app-main">
        {selectedCollection ? (
          <CollectionDetails
            collection={selectedCollection}
            onBack={handleBackFromDetails}
            onNavChange={setNavItems}
            searchQuery={searchQuery}
          />
        ) : (
          <Collections onSelectCollection={handleSelectCollection} searchQuery={searchQuery} />
        )}
      </main>
    </div>
  );
}
