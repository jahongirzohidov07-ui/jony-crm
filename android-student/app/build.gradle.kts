plugins {
    id("com.android.application")
}

// IMZO (2026-10-07). Kalit repozitoriyda TURMAYDI: GitHub Actions uni
// Secrets'dan vaqtincha faylga yozadi va shu o'zgaruvchilar orqali
// beradi. Mahalliy yig'ishda o'zgaruvchilar bo'lmasa — imzosiz release.
val ksFile = System.getenv("JONY_KEYSTORE_FILE")

android {
    namespace = "uz.jonyos.jonystudent"
    compileSdk = 36

    defaultConfig {
        // Play'dagi ilova bilan BIR XIL paket — oddiy yangilanish
        applicationId = "uz.jonyos.jonystudent"
        minSdk = 24
        targetSdk = 36
        // 1-versiya (PWABuilder) versionCode=1 edi; yangisi kattaroq
        // bo'lishi shart. Har yangi relizda oshiriladi.
        versionCode = 20
        versionName = "2.0.0"
    }

    signingConfigs {
        if (ksFile != null) {
            create("upload") {
                storeFile = file(ksFile)
                storePassword = System.getenv("JONY_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("JONY_KEY_ALIAS")
                keyPassword = System.getenv("JONY_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            if (ksFile != null) {
                signingConfig = signingConfigs.getByName("upload")
            }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    // Kameradan olingan rasmni sahifaga uzatish uchun FileProvider
    implementation("androidx.core:core:1.16.0")
    // Ilova yopiq bo'lsa ham bildirishnomalarni tekshirish (har 15 daq.)
    implementation("androidx.work:work-runtime:2.10.1")
}
