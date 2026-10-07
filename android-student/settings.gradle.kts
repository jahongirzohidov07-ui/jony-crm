// JONY STUDENT — Android ilovasi, 2-versiya (2026-10-07).
//
// Jahongir: "butun app bo'yicha screenshot mumkin bo'lmasin, ilovada
// offline rejimda ham mashqlar ishlash mumkin bo'lsin, bildirishnomalar
// ham keladigan bo'lsin".
//
// 1-versiya (PWABuilder TWA) saytni Chrome ichida ochardi — u yerda
// skrinshotni yopib bo'lmaydi. Bu versiya saytni ilovaning O'Z
// WebView'ida ochadi: butun ilovada FLAG_SECURE, ovoz/nutq ko'prigi,
// fon bildirishnomalari. Paket nomi o'sha — uz.jonyos.jonystudent,
// o'quvchilarda oddiy yangilanish bo'lib tushadi.
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "jony-student"
include(":app")
