import { useState } from "react";
import Collections from "./Collections";
import CollectionDetails from "./CollectionDetails";

interface Collection {
  id: string;
  name: string;
  owner_id: string;
  created_at: string;
}

export default function App() {
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null);

  return (
    <div className="app">
      <main className="app-main">
        {selectedCollection ? (
          <CollectionDetails
            collection={selectedCollection}
            onBack={() => setSelectedCollection(null)}
          />
        ) : (
          <Collections onSelectCollection={setSelectedCollection} />
        )}
      </main>
    </div>
  );
}
