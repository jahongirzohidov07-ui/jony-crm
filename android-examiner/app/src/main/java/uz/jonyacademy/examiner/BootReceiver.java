package uz.jonyacademy.examiner;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Telefon qayta yoqilganda kuzatuv o'zi tiklanadi (2026-09-25). */
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context c, Intent i) {
        Api.init(c);
        if (Api.token(c) != null) {
            WatchService.start(c);
        }
    }
}
