import { Capacitor } from "@capacitor/core";
import { BarcodeFormat, BarcodeScanner } from "@capacitor-mlkit/barcode-scanning";

import { isFiscalReceiptQr, normalizeQrPayload } from "@/lib/qr-payload";

export function isNativeApp(): boolean {
  return Capacitor.isNativePlatform();
}

/** Сканирование камерой в Capacitor (Android / iOS). */
export async function scanReceiptQrNative(): Promise<string> {
  const { supported } = await BarcodeScanner.isSupported();
  if (!supported) {
    throw new Error("Камера недоступна на этом устройстве");
  }

  if (Capacitor.getPlatform() === "android") {
    const { available } = await BarcodeScanner.isGoogleBarcodeScannerModuleAvailable();
    if (!available) {
      await BarcodeScanner.installGoogleBarcodeScannerModule();
    }
  }

  const perms = await BarcodeScanner.checkPermissions();
  if (perms.camera !== "granted" && perms.camera !== "limited") {
    const req = await BarcodeScanner.requestPermissions();
    if (req.camera !== "granted" && req.camera !== "limited") {
      throw new Error("Нет доступа к камере. Разрешите в настройках приложения.");
    }
  }

  const { barcodes } = await BarcodeScanner.scan({
    formats: [BarcodeFormat.QrCode],
  });

  const raw = barcodes[0]?.rawValue ?? barcodes[0]?.displayValue ?? "";
  const payload = normalizeQrPayload(raw);
  if (!isFiscalReceiptQr(payload)) {
    throw new Error("Это не QR фискального чека. Наведите на QR с чека.");
  }
  return payload;
}
