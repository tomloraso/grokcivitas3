/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useCallback, type ReactNode } from "react";

export interface SearchSnapshot {
  postcode: string;
  radius: number;
  count: number;
}

interface SearchContextValue {
  search: SearchSnapshot | null;
  setSearch: (snapshot: SearchSnapshot) => void;
  clearSearch: () => void;
}

const SearchCtx = createContext<SearchContextValue>({
  search: null,
  setSearch: () => {},
  clearSearch: () => {},
});

export function useSearchContext(): SearchContextValue {
  return useContext(SearchCtx);
}

export function SearchContextProvider({
  children,
  initialSearch = null,
}: {
  children: ReactNode;
  /** Pre-populated search snapshot (useful for testing) */
  initialSearch?: SearchSnapshot | null;
}): JSX.Element {
  const [search, setSearchState] = useState<SearchSnapshot | null>(initialSearch);

  const setSearch = useCallback((snapshot: SearchSnapshot) => {
    setSearchState(snapshot);
  }, []);

  const clearSearch = useCallback(() => {
    setSearchState(null);
  }, []);

  return (
    <SearchCtx.Provider value={{ search, setSearch, clearSearch }}>
      {children}
    </SearchCtx.Provider>
  );
}
