type Listener = () => void;

const accountsListeners = new Set<Listener>();
const transactionsListeners = new Set<Listener>();

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
