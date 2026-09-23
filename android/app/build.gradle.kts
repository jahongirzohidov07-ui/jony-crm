plugins {
    id("com.android.application")
}

android {
    namespace = "uz.jonyacademy.exam"
    compileSdk {
        version = release(36) {
            minorApiLevel = 1
        }
    }

    defaultConfig {
        applicationId = "uz.jonyacademy.exam"
        // Android 8 va undan yuqori — bugungi telefonlarning deyarli
        // hammasi. Pastroq versiyada FLAG_SECURE ham ishonchsiz.
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            optimization {
                enable = false
            }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}

dependencies {
    // Kameradan olingan rasmni sahifaga uzatish uchun FileProvider
    implementation("androidx.core:core:1.16.0")
}
