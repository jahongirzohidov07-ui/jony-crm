plugins {
    id("com.android.application")
}

android {
    namespace = "uz.jonyacademy.examiner"
    compileSdk {
        version = release(36) {
            minorApiLevel = 1
        }
    }

    defaultConfig {
        applicationId = "uz.jonyacademy.examiner"
        minSdk = 26
        targetSdk = 36
        versionCode = 3
        versionName = "1.2"
    }

    buildTypes {
        release {
            optimization {
                enable = false
            }
        }
    }
    lint {
        // local.properties har kompyuterda o'zicha va git'ga kirmaydi
        disable += "PropertyEscape"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}

dependencies {
    implementation("androidx.core:core:1.16.0")
}
