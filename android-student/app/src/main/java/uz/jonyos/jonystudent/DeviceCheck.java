package uz.jonyos.jonystudent;

import android.os.Build;

import java.io.File;

/**
 * QURILMA TEKSHIRUVI.
 *
 * <p>Skrinshotni to'suvchi FLAG_SECURE ni faqat ikki xil qurilmada
 * aylanib o'tish mumkin: root qilingan telefonda va kompyuterdagi
 * emulyatorda. Shuning uchun test bunday qurilmada ochilmaydi â€”
 * o'quvchi oddiy telefonidan kiradi.
 */
final class DeviceCheck {

    private DeviceCheck() {
    }

    /** Root topilsa â€” sabab matni, toza bo'lsa â€” null. */
    static String problem() {
        if (rooted()) {
            return "Bu telefon root qilingan. Imtihon bunday "
                    + "qurilmada ochilmaydi â€” boshqa telefondan kiring "
                    + "yoki examinerga ayting.";
        }
        if (emulator()) {
            return "Imtihon kompyuterdagi emulyatorda emas, haqiqiy "
                    + "telefonda yechiladi.";
        }
        return null;
    }

    private static boolean rooted() {
        String tags = Build.TAGS;
        if (tags != null && tags.contains("test-keys")) {
            return true;
        }
        String[] paths = {
                "/system/bin/su", "/system/xbin/su", "/sbin/su",
                "/system/su", "/su/bin/su", "/data/local/su",
                "/data/local/bin/su", "/data/local/xbin/su",
                "/system/app/Superuser.apk", "/sbin/magisk",
                "/data/adb/magisk", "/data/adb/modules",
        };
        for (String p : paths) {
            if (new File(p).exists()) {
                return true;
            }
        }
        return false;
    }

    private static boolean emulator() {
        String fp = String.valueOf(Build.FINGERPRINT);
        String model = String.valueOf(Build.MODEL);
        String product = String.valueOf(Build.PRODUCT);
        String brand = String.valueOf(Build.BRAND);
        String device = String.valueOf(Build.DEVICE);
        return fp.startsWith("generic")
                || fp.startsWith("unknown")
                || fp.contains("emulator")
                || model.contains("google_sdk")
                || model.contains("Emulator")
                || model.contains("Android SDK built for")
                || product.contains("sdk_gphone")
                || product.equals("google_sdk")
                || product.contains("vbox")
                || String.valueOf(Build.MANUFACTURER).contains("Genymotion")
                || (brand.startsWith("generic") && device.startsWith("generic"));
    }
}
