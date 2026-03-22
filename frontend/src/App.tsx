// about the main app component
// this is the rort react component that acts like a page router
//  for this program.
// it uses a selected collection state variable to track whicj collection the user clicked on. .when nothing is selcted , 
// it shows he collectios component ( the list of al collections in the professor currenlty have)
// when the user clicks a collection, it shows the collection deatus compaonent( like the dataset in a collection)
// on back call back lets users go back to the collections list view .
// it is a navigation toggle between " see all ollections and see deatils of one coletion"

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
