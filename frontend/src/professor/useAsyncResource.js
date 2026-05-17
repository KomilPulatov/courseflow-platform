import { useEffect, useState } from "react";

export function useAsyncResource(loader, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let active = true;

    async function run() {
      setLoading(true);
      setError("");
      try {
        const result = await loader();
        if (!active) return;
        setData(result);
      } catch (loadError) {
        if (!active) return;
        setError(loadError.message);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    run();
    return () => {
      active = false;
    };
  }, [...deps, reloadToken]);

  return {
    data,
    loading,
    error,
    reload: () => setReloadToken((value) => value + 1),
  };
}
