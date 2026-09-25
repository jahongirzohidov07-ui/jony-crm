// JONY IMTIHON — Android ilovasi (2026-09-23).
//
// Ilova o'zi test yozmaydi: ichida CRM'dagi o'sha test sahifasi
// ochiladi. Ilovaning butun vazifasi — brauzerda qilib bo'lmaydigan
// himoya: skrinshotni butunlay to'sish, ekranni qulflash va
// root/emulyatorni rad etish.
pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
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

rootProject.name = "jony-examiner"
include(":app")
