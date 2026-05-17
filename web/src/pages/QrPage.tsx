import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Camera, ScanLine } from "lucide-react";
import { api, formatMoney, type Account, type TransactionDetail } from "@/api/client";
import { ApiError } from "@/api/client";
import { QrCameraScanner } from "@/components/QrCameraScanner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { isNativeApp, scanReceiptQrNative } from "@/lib/qr-scanner";

export default function QrPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountId, setAccountId] = useState("");
  const [qr, setQr] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [result, setResult] = useState<TransactionDetail | null>(null);

  useEffect(() => {
    api.accounts().then((r) => {
      setAccounts(r.accounts);
      if (r.accounts[0]) setAccountId(r.accounts[0].id);
    });
  }, []);

  const uploadReceipt = useCallback(
    async (qrPayload: string) => {
      setError("");
      setResult(null);
      setLoading(true);
      try {
        const res = await api.scanQr({ account_id: accountId, qr: qrPayload.trim() });
        setResult(res.transaction);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Ошибка");
      } finally {
        setLoading(false);
      }
    },
    [accountId]
  );

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    await uploadReceipt(qr);
  };

  const scanWithCamera = async () => {
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
      <Link to="/" className="mb-4 inline-flex items-center gap-2 text-sm text-neutral-500 hover:text-neutral-900">
        <ArrowLeft size={16} /> Назад
      </Link>
      <header className="mb-6">
        <h1 className="text-2xl font-semibold">Сканировать чек</h1>
        <p className="mt-1 text-neutral-500">
          Сканируйте QR камерой или вставьте строку вручную
        </p>
      </header>

      {error && (
        <p className="mb-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      <Card className="max-w-xl rounded-3xl">
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <label className="block">
              <span className="mb-1.5 block text-sm text-neutral-500">Счёт</span>
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

            <Button
              type="button"
              variant="outline"
              className="w-full gap-2"
              disabled={loading || scanning || !accountId}
              onClick={() => void scanWithCamera()}
            >
              <Camera size={16} />
              {scanning ? "Сканирование..." : "Сканировать камерой"}
            </Button>

            <label className="block">
              <span className="mb-1.5 block text-sm text-neutral-500">QR-строка</span>
              <textarea
                className="input-field min-h-[120px] resize-y"
                value={qr}
                onChange={(e) => setQr(e.target.value)}
                placeholder="t=20260517T1419&s=1387.50&fn=..."
              />
            </label>
            <Button
              type="submit"
              className="w-full gap-2"
              disabled={loading || scanning || !accountId || !qr.trim()}
            >
              <ScanLine size={16} />
              {loading ? "Обработка чека..." : "Загрузить чек"}
            </Button>
          </form>

          {result && (
            <div className="mt-6 border-t border-neutral-100 pt-6">
              <h3 className="mb-4 text-lg font-semibold">
                {result.merchant?.name} — {formatMoney(result.amount)}
              </h3>
              <ul className="space-y-3">
                {result.items?.map((item, i) => (
                  <li
                    key={i}
                    className="flex items-center justify-between border-b border-neutral-50 py-2 last:border-0"
                  >
                    <span className="text-sm">{item.raw_name}</span>
                    <span className="text-right text-sm font-semibold">
                      {formatMoney(item.amount)}
                      {item.category?.name && (
                        <Badge className="ml-2">{item.category.name}</Badge>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      <QrCameraScanner
        open={cameraOpen}
        onClose={() => setCameraOpen(false)}
        onScan={onWebScan}
      />
    </>
  );
}
