// about the main app component
// this is the rort react component that acts like a page router
//  for this program.
// it uses a selected collection state variable to track whicj collection the user clicked on. .when nothing is selcted , 
// it shows he collectios component ( the list of al collections in the professor currenlty have)
// when the user clicks a collection, it shows the collection deatus compaonent( like the dataset in a collection)
// on back call back lets users go back to the collections list view .
// it is a navigation toggle between " see all ollections and see deatils of one coletion"

import { useEffect, useState } from "react";
import Collections from "./Collections";
import CollectionDetails from "./CollectionDetails";

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

export default function App() {
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [navItems, setNavItems] = useState<NavItem[]>([{ label: "Collections", active: true }]);

  const showCollections = (e?: React.MouseEvent) => {
    e?.preventDefault();
    setSelectedCollection(null);
  };

  useEffect(() => {
    if (!selectedCollection) {
      setNavItems([{ label: "Collections", active: true }]);
    }
  }, [selectedCollection]);

  return (
    <div className="app app-shell">
      <header className="site-nav navbar">
        <div className="site-nav-inner">
          <div className="nav-left">
            <button type="button" className="site-title brand-link" onClick={showCollections}>
              Plagiarism Detector
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
              className="nav-search search"
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
            onBack={() => setSelectedCollection(null)}
            onNavChange={setNavItems}
            searchQuery={searchQuery}
          />
        ) : (
          <Collections onSelectCollection={setSelectedCollection} searchQuery={searchQuery} />
        )}
      </main>
    </div>
  );
}
