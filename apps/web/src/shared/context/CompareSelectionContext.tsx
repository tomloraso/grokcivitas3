/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export interface CompareSelectionItem {
  urn: string;
  name: string;
  phase: string | null;
  type: string | null;
  postcode: string | null;
  distanceMiles?: number;
  source: "search" | "profile" | "compare";
}

export type CompareSelectionResult = "added" | "duplicate" | "limit";

interface CompareSelectionContextValue {
  items: CompareSelectionItem[];
  count: number;
  isHydrated: boolean;
  hasSchool: (urn: string) => boolean;
  getSchool: (urn: string) => CompareSelectionItem | null;
  addSchool: (item: CompareSelectionItem) => CompareSelectionResult;
  replaceSchools: (items: CompareSelectionItem[]) => void;
  upsertSchools: (items: CompareSelectionItem[]) => void;
  removeSchool: (urn: string) => void;
  clearSchools: () => void;
}

const STORAGE_KEY = "civitas.compare.selection";

const CompareSelectionCtx = createContext<CompareSelectionContextValue>({
  items: [],
  count: 0,
  isHydrated: false,
  hasSchool: () => false,
  getSchool: () => null,
  addSchool: () => "added",
  replaceSchools: () => {},
  upsertSchools: () => {},
  removeSchool: () => {},
  clearSchools: () => {},
});

export function useCompareSelection(): CompareSelectionContextValue {
  return useContext(CompareSelectionCtx);
}

export function CompareSelectionProvider({
  children,
  initialItems = [],
}: {
  children: ReactNode;
  initialItems?: CompareSelectionItem[];
}): JSX.Element {
  const [items, setItems] = useState<CompareSelectionItem[]>(initialItems);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") {
      setIsHydrated(true);
      return;
    }

    const rawValue = window.localStorage.getItem(STORAGE_KEY);
    if (!rawValue) {
      setIsHydrated(true);
      return;
    }

    try {
      const parsed = JSON.parse(rawValue) as CompareSelectionItem[];
      if (Array.isArray(parsed)) {
        setItems(parsed);
      }
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
    } finally {
      setIsHydrated(true);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    if (!isHydrated) {
      return;
    }
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }, [isHydrated, items]);

  const hasSchool = useCallback(
    (urn: string) => items.some((item) => item.urn === urn),
    [items]
  );

  const getSchool = useCallback(
    (urn: string) => items.find((item) => item.urn === urn) ?? null,
    [items]
  );

  const addSchool = useCallback((item: CompareSelectionItem): CompareSelectionResult => {
    let result: CompareSelectionResult = "added";
    setItems((current) => {
      if (current.some((entry) => entry.urn === item.urn)) {
        result = "duplicate";
        return current;
      }
      if (current.length >= 4) {
        result = "limit";
        return current;
      }
      return [...current, item];
    });
    return result;
  }, []);

  const replaceSchools = useCallback((nextItems: CompareSelectionItem[]) => {
    setItems(nextItems.slice(0, 4));
  }, []);

  const upsertSchools = useCallback((nextItems: CompareSelectionItem[]) => {
    setItems((current) => {
      const merged = [...current];
      for (const nextItem of nextItems) {
        const existingIndex = merged.findIndex((item) => item.urn === nextItem.urn);
        if (existingIndex >= 0) {
          merged[existingIndex] = { ...merged[existingIndex], ...nextItem };
          continue;
        }
        if (merged.length >= 4) {
          break;
        }
        merged.push(nextItem);
      }
      return merged;
    });
  }, []);

  const removeSchool = useCallback((urn: string) => {
    setItems((current) => current.filter((item) => item.urn !== urn));
  }, []);

  const clearSchools = useCallback(() => {
    setItems([]);
  }, []);

  const value = useMemo(
    () => ({
      items,
      count: items.length,
      isHydrated,
      hasSchool,
      getSchool,
      addSchool,
      replaceSchools,
      upsertSchools,
      removeSchool,
      clearSchools,
    }),
    [
      addSchool,
      clearSchools,
      getSchool,
      hasSchool,
      isHydrated,
      items,
      removeSchool,
      replaceSchools,
      upsertSchools
    ]
  );

  return <CompareSelectionCtx.Provider value={value}>{children}</CompareSelectionCtx.Provider>;
}
