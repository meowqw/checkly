import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Camera, ChevronRight, ScanLine, WifiOff } from "lucide-react";
import * as data from "@/api/data-service";
import { formatMoney, type TransactionDetail, type TransactionItem } from "@/api/client";
import { ApiError } from "@/api/client";
import { useAccounts } from "@/context/AccountsContext";
import { ItemCategorySheet } from "@/components/ItemCategorySheet";
import { NoAccountsNotice } from "@/components/NoAccountsNotice";
import { QrCameraScanner } from "@/components/QrCameraScanner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useSync } from "@/context/SyncContext";
import { isNativeApp, scanReceiptQrNative } from "@/lib/qr-scanner";

export default function QrPage() {
  const { online } = useSync();
  const { accounts, loading: accountsLoading } = useAccounts();
  const [accountId, setAccountId] = useState("");
  const [qr, setQr] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [result, setResult] = useState<TransactionDetail | null>(null);
  const [editItem, setEditItem] = useState<TransactionItem | null>(null);

  useEffect(() => {
    if (accounts[0] && !accountId) setAccountId(accounts[0].id);
  }, [accounts, accountId]);

  const uploadReceipt = useCallback(
    async (qrPayload: string) => {
      if (!online) {
        setError("Сканирование чеков доступно только при подключении к интернету");
        return;
      }
      setError("");
      setResult(null);
      setLoading(true);
      try {
        const res = await data.scanQr({ account_id: accountId, qr: qrPayload.trim() });
        setResult(res.transaction);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Ошибка");
      } finally {
        setLoading(false);
      }
    },
    [accountId, online]
  );

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    await uploadReceipt(qr);
  };

  const scanWithCamera = async () => {
    if (!online) {
      setError("Сканирование чеков доступно только при подключении к интернету");
      return;
    }
    setError("");
    if (isNativeApp()) {
      setScanning(true);
      try {
        const payload = await scanReceiptQrNative();
        setQr(payload);
        await uploadReceipt(payload);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Не удалось отсканировать");
      } finally {
        setScanning(false);
      }
      return;
    }
    setCameraOpen(true);
  };

  const onWebScan = (payload: string) => {
    setQr(payload);
    void uploadReceipt(payload);
  };

  return (
    <>
      <Link
        to="/"
        className="mb-3 inline-flex items-center gap-1.5 text-sm text-neutral-500 active:text-neutral-900"
      >
        <ArrowLeft size={16} /> Назад
      </Link>

      <header className="mb-4">
        <h1 className="text-lg font-semibold">Сканировать чек</h1>
        <p className="mt-0.5 text-xs text-neutral-400">QR камерой или вручную</p>
      </header>

      {!online && (
        <p className="mb-3 flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          <WifiOff size={16} />
          Без интернета чеки недоступны. Ручные операции работают из кэша.
        </p>
      )}

      {error && (
        <p className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {!accountsLoading && accounts.length === 0 ? (
        <NoAccountsNotice />
      ) : (
      <form onSubmit={submit} className="space-y-3">
        {accounts.length > 1 && (
          <label className="block">
            <span className="mb-1 block text-xs text-neutral-500">Счёт</span>
            <select
              className="input-field"
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              required
            >
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </label>
        )}

        <Button
          type="button"
          variant="brand"
          className="w-full gap-2"
          size="lg"
          disabled={!online || loading || scanning || !accountId}
          onClick={() => void scanWithCamera()}
        >
          <Camera size={18} />
          {scanning ? "Сканирование..." : "Открыть камеру"}
        </Button>

        <label className="block">
          <span className="mb-1 block text-xs text-neutral-500">Или вставьте QR-строку</span>
          <textarea
            className="input-field min-h-[88px] resize-y font-mono text-xs"
            value={qr}
            onChange={(e) => setQr(e.target.value)}
            placeholder="t=20260517T1419&s=1387.50&fn=..."
            disabled={!online}
          />
        </label>

        <Button
          type="submit"
          variant="outline"
          className="w-full gap-2"
          disabled={!online || loading || scanning || !accountId || !qr.trim()}
        >
          <ScanLine size={16} />
          {loading ? "Обработка..." : "Загрузить"}
        </Button>
      </form>
      )}

      {result && (
        <div className="mt-5 border-t border-neutral-100 pt-4">
          <h3 className="mb-1 text-base font-semibold">
            {result.merchant?.name}{" "}
            <span className="text-brand">{formatMoney(result.amount)}</span>
          </h3>
          <p className="mb-3 text-xs text-neutral-400">Нажмите на позицию, чтобы изменить категорию</p>
          <ul className="list-divider">
            {result.items?.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => item.id && setEditItem(item)}
                  className="flex w-full items-center justify-between gap-2 py-2.5 text-left active:bg-neutral-50"
                >
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm">{item.raw_name}</span>
                    {item.category?.name && (
                      <Badge className="mt-1">{item.category.name}</Badge>
                    )}
                  </span>
                  <span className="flex shrink-0 items-center gap-1 text-sm font-semibold tabular-nums">
                    {formatMoney(item.amount)}
                    <ChevronRight size={14} className="text-neutral-300" />
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <ItemCategorySheet
        open={!!editItem}
        transactionId={result?.id ?? ""}
        item={editItem}
        onClose={() => setEditItem(null)}
        onSaved={(tx) => setResult(tx)}
      />

      <QrCameraScanner
        open={cameraOpen}
        onClose={() => setCameraOpen(false)}
        onScan={onWebScan}
      />
    </>
  );
}
