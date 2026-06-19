/** Дождаться фоновой синхронизации и показать RefreshBar. */
export function trackBackgroundFresh(
  results: { fresh?: Promise<void> }[],
  setRefreshing: (value: boolean) => void
) {
  const promises = results.map((r) => r.fresh).filter(Boolean) as Promise<void>[];
  if (promises.length === 0) return;
  setRefreshing(true);
  Promise.all(promises).finally(() => setRefreshing(false));
}
