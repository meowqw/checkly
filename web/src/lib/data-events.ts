type Listener = () => void;

const accountsListeners = new Set<Listener>();
const transactionsListeners = new Set<Listener>();
const categoriesListeners = new Set<Listener>();

export function subscribeAccountsChanged(listener: Listener): () => void {
  accountsListeners.add(listener);
  return () => accountsListeners.delete(listener);
}

export function notifyAccountsChanged() {
  accountsListeners.forEach((fn) => fn());
}

export function subscribeTransactionsChanged(listener: Listener): () => void {
  transactionsListeners.add(listener);
  return () => transactionsListeners.delete(listener);
}

export function notifyTransactionsChanged() {
  transactionsListeners.forEach((fn) => fn());
}

export function subscribeCategoriesChanged(listener: Listener): () => void {
  categoriesListeners.add(listener);
  return () => categoriesListeners.delete(listener);
}

export function notifyCategoriesChanged() {
  categoriesListeners.forEach((fn) => fn());
}
